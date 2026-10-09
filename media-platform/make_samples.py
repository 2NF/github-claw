"""Generate small sample media files into ./samples (requires Pillow + ffmpeg)."""
import os
import subprocess
from PIL import Image, ImageDraw

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
os.makedirs(out, exist_ok=True)
img = Image.new("RGB", (1200, 800))
d = ImageDraw.Draw(img)
for y in range(800):
    d.line([(0, y), (1200, y)], fill=(y % 256, (y * 2) % 256, 180))
d.ellipse((300, 200, 900, 600), outline=(255, 255, 255), width=12)
img.save(os.path.join(out, "sample.png"))
img.save(os.path.join(out, "sample.jpg"), quality=95)


def ff(*a):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *a], check=True)


ff("-f", "lavfi", "-i", "sine=frequency=440:duration=3", os.path.join(out, "sample.wav"))
ff("-f", "lavfi", "-i", "testsrc=duration=2:size=640x360:rate=24", "-f", "lavfi", "-i", "sine=frequency=330:duration=2",
   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", os.path.join(out, "sample.mp4"))
print("samples written to", out)
