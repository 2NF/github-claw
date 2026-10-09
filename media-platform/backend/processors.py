"""Media processing: Pillow for images, FFmpeg for audio/video."""
import os
import shutil
import subprocess

from PIL import Image

IMAGE_FORMATS = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP", "bmp": "BMP", "gif": "GIF"}
AUDIO_FORMATS = ["mp3", "wav", "aac", "ogg", "flac", "m4a"]
VIDEO_FORMATS = ["mp4", "webm", "mkv", "avi", "mov", "gif"]
IMAGE_INPUT = {"jpg", "jpeg", "png", "webp", "bmp", "gif", "tiff"}
AUDIO_INPUT = set(AUDIO_FORMATS) | {"wma", "opus"}
VIDEO_INPUT = {"mp4", "webm", "mkv", "avi", "mov", "flv", "wmv", "m4v"}

OUTPUT_FORMATS = {
    "image": ["jpg", "png", "webp", "bmp", "gif"],
    "audio": AUDIO_FORMATS,
    "video": VIDEO_FORMATS,
}


class ProcessingError(Exception):
    pass


def detect_kind(filename):
    ext = os.path.splitext(filename)[1].lstrip(".").lower()
    if ext in IMAGE_INPUT:
        return "image"
    if ext in AUDIO_INPUT:
        return "audio"
    if ext in VIDEO_INPUT:
        return "video"
    return None


def ffmpeg_path():
    return shutil.which("ffmpeg")


def _int(params, key, default=None, lo=None, hi=None):
    v = params.get(key)
    if v in (None, ""):
        return default
    try:
        v = int(v)
    except (TypeError, ValueError):
        raise ProcessingError(f"参数 {key} 必须是整数")
    if lo is not None and v < lo or hi is not None and v > hi:
        raise ProcessingError(f"参数 {key} 超出范围 [{lo}, {hi}]")
    return v


def process_image(src, dst, fmt, params):
    quality = _int(params, "quality", 80, 1, 100)
    max_width = _int(params, "max_width", None, 1, 20000)
    try:
        img = Image.open(src)
        img.load()
    except Exception as e:
        raise ProcessingError("无法读取图片，文件可能已损坏")
    if max_width and img.width > max_width:
        h = max(1, round(img.height * max_width / img.width))
        img = img.resize((max_width, h), Image.LANCZOS)
    pil_fmt = IMAGE_FORMATS[fmt]
    kwargs = {}
    if pil_fmt == "JPEG":
        if img.mode != "RGB":
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGBA")
                bg = Image.new("RGB", img.size, (255, 255, 255))
                bg.paste(img, mask=img.split()[-1])
                img = bg
            else:
                img = img.convert("RGB")
        kwargs = {"quality": quality, "optimize": True}
    elif pil_fmt == "WEBP":
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.mode or img.mode == "P" else "RGB")
        kwargs = {"quality": quality}
    elif pil_fmt == "PNG":
        kwargs = {"optimize": True, "compress_level": 9}
        if quality < 100 and params.get("action") == "compress":
            # lossy PNG compression via palette quantization
            img = img.convert("RGBA").quantize(256) if "A" in img.mode else img.convert("RGB").quantize(256)
    elif pil_fmt == "BMP":
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
    elif pil_fmt == "GIF":
        if img.mode not in ("P", "L"):
            img = img.convert("RGB").quantize(256)
    img.save(dst, pil_fmt, **kwargs)


def _run_ffmpeg(args):
    exe = ffmpeg_path()
    if not exe:
        raise ProcessingError("未找到 FFmpeg，请先安装")
    cmd = [exe, "-y", "-hide_banner", "-loglevel", "error", "-nostdin"] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    except subprocess.TimeoutExpired:
        raise ProcessingError("处理超时")
    if r.returncode != 0:
        raise ProcessingError("FFmpeg 失败: " + (r.stderr.strip()[-500:] or "未知错误"))


AUDIO_CODECS = {
    "mp3": ["-c:a", "libmp3lame"],
    "wav": ["-c:a", "pcm_s16le"],
    "aac": ["-c:a", "aac"],
    "m4a": ["-c:a", "aac"],
    "ogg": ["-c:a", "libvorbis"],
    "flac": ["-c:a", "flac"],
}


def process_audio(src, dst, fmt, params):
    bitrate = _int(params, "bitrate", 128, 16, 512)
    sample_rate = _int(params, "sample_rate", None, 8000, 192000)
    args = ["-i", src, "-vn"] + AUDIO_CODECS[fmt]
    if fmt not in ("wav", "flac"):
        args += ["-b:a", f"{bitrate}k"]
    if sample_rate:
        args += ["-ar", str(sample_rate)]
    _run_ffmpeg(args + [dst])


def process_video(src, dst, fmt, params):
    crf = _int(params, "crf", 28, 0, 51)
    height = _int(params, "height", None, 16, 4320)
    vf = []
    if height:
        vf.append(f"scale=-2:{height}")
    if fmt == "gif":
        vf = [f"fps=10,scale=-2:{height or 360}:flags=lanczos"]
        _run_ffmpeg(["-i", src, "-an", "-vf", ",".join(vf), dst])
        return
    args = ["-i", src]
    if vf:
        args += ["-vf", ",".join(vf)]
    if fmt == "webm":
        args += ["-c:v", "libvpx-vp9", "-crf", str(crf), "-b:v", "0", "-deadline", "realtime", "-cpu-used", "8",
                 "-c:a", "libopus"]
    elif fmt == "avi":
        args += ["-c:v", "mpeg4", "-q:v", str(max(2, min(31, crf // 2 + 1))), "-c:a", "libmp3lame"]
    else:
        args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p", "-c:a", "aac",
                 "-b:a", "128k"]
        if fmt in ("mp4", "mov"):
            args += ["-movflags", "+faststart"]
    _run_ffmpeg(args + [dst])


def process(kind, src, dst, fmt, params):
    if fmt not in OUTPUT_FORMATS[kind]:
        raise ProcessingError(f"不支持的目标格式: {fmt}")
    {"image": process_image, "audio": process_audio, "video": process_video}[kind](src, dst, fmt, params)
