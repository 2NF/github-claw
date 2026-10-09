import os
import subprocess
import sys
import time

import pytest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    return create_app(str(tmp_path)).test_client()


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)


@pytest.fixture
def files(tmp_path):
    img = Image.new("RGBA", (400, 300), (10, 120, 200, 128))
    img.save(tmp_path / "a.png")
    ff("-f", "lavfi", "-i", "sine=frequency=440:duration=1", str(tmp_path / "a.wav"))
    ff("-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=15", "-f", "lavfi", "-i", "sine=duration=1",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(tmp_path / "a.mp4"))
    return tmp_path


def submit(client, path, **form):
    with open(path, "rb") as fh:
        form["file"] = (fh, os.path.basename(path))
        r = client.post("/api/tasks", data=form, content_type="multipart/form-data")
    assert r.status_code == 201, r.json
    tid = r.json["id"]
    for _ in range(120):
        t = client.get(f"/api/tasks/{tid}").json
        if t["status"] in ("done", "failed"):
            return t
        time.sleep(0.5)
    raise AssertionError("timeout")


@pytest.mark.parametrize("fmt", ["jpg", "webp", "bmp", "gif", "png"])
def test_image_convert(client, files, fmt):
    t = submit(client, files / "a.png", action="convert", target_format=fmt, kind="image")
    assert t["status"] == "done", t
    r = client.get(f"/api/tasks/{t['id']}/download")
    assert r.status_code == 200 and len(r.data) > 0


def test_image_compress_resize(client, files, tmp_path):
    t = submit(client, files / "a.png", action="compress", target_format="jpg", quality="30", max_width="100")
    assert t["status"] == "done"
    out = tmp_path / "o.jpg"
    out.write_bytes(client.get(f"/api/tasks/{t['id']}/download").data)
    assert Image.open(out).width == 100


@pytest.mark.parametrize("fmt", ["mp3", "wav", "aac", "ogg", "flac", "m4a"])
def test_audio_convert(client, files, fmt):
    t = submit(client, files / "a.wav", action="convert", target_format=fmt)
    assert t["status"] == "done", t


def test_audio_compress(client, files):
    t = submit(client, files / "a.wav", action="compress", target_format="mp3", bitrate="64")
    assert t["status"] == "done" and t["output_size"] < t["input_size"]


@pytest.mark.parametrize("fmt", ["mp4", "webm", "mkv", "avi", "mov", "gif"])
def test_video_convert(client, files, fmt):
    t = submit(client, files / "a.mp4", action="convert", target_format=fmt)
    assert t["status"] == "done", t


def test_video_compress(client, files):
    t = submit(client, files / "a.mp4", action="compress", crf="35", height="120")
    assert t["status"] == "done"


def test_errors_and_lifecycle(client, files):
    assert client.post("/api/tasks", data={}).status_code == 400
    bad = files / "x.txt"
    bad.write_text("hi")
    with open(bad, "rb") as fh:
        assert client.post("/api/tasks", data={"file": (fh, "x.txt")}).status_code == 400
    corrupt = files / "c.png"
    corrupt.write_text("not an image")
    t = submit(client, corrupt, action="convert", target_format="jpg")
    assert t["status"] == "failed" and t["error"]
    t = submit(client, files / "a.png", action="compress", quality="999")
    assert t["status"] == "failed"
    assert len(client.get("/api/tasks").json) == 2
    assert client.get("/api/stats").json
    assert client.delete(f"/api/tasks/{t['id']}").status_code == 200
    assert client.get(f"/api/tasks/{t['id']}").status_code == 404
