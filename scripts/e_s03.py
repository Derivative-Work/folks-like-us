"""E: S03, the Suno screen, cut from [H]'s screen recording (config/edit.json "s03").

The recording (macOS, 3074x2118 at 120 fps) shows the lyrics and the style prompt pasted into Suno, "Create" clicked,
the two takes generating, and one played. Each beat is one or more stretches of it ("spans", seconds), played in real
time and joined by jump cuts, cropped to the one panel that matters ("crop", recording pixels):
the account name in the sidebar and the player bar, the other projects in the song list and the browser chrome stay
out of frame. The crop is scaled to fit inside the margin and centred on Suno's own background colour, with a slow
push-in per beat. The recording is variable-frame-rate: frames are taken by time (ffmpeg's fps filter), never by index.

Output: takes/s03/s03.mp4 (1920x1080, 24 fps; git-ignored), which e_edit.py cuts in at the intro's S03 frames.
Usage: .venv/bin/python scripts/e_s03.py
"""
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

CFG = json.load(open("config/edit.json"))
FPS = 24
OUT = Path("takes/s03/s03.mp4")


def beat_frames(src, t0, t1, crop, n):
    """n frames evenly through [t0, t1) of the recording, cropped."""
    x0, y0, x1, y1 = (v - v % 2 for v in crop)  # the recording is 4:2:0: ffmpeg crops on even pixels
    w, h = x1 - x0, y1 - y0
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t0:.3f}", "-i", src, "-t", f"{t1 - t0:.3f}",
                          "-vf", f"crop={w}:{h}:{x0}:{y0},fps={n / (t1 - t0):.6f}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    v = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    return [Image.fromarray(v[min(i, len(v) - 1)]) for i in range(n)]


def main():
    c = CFG["s03"]
    W, H = CFG["size"]
    fw, fh = c["fit"]
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(OUT)],
                         stdin=subprocess.PIPE)
    total = 0
    for b in c["beats"]:
        frames = [im for t0, t1 in b["spans"]
                  for im in beat_frames(c["source"], t0, t1, b["crop"], round((t1 - t0) * FPS))]
        for i, im in enumerate(frames):
            z = 1 + c["push"] * i / max(1, len(frames) - 1)
            s = min(fw / im.width, fh / im.height) * z
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            canvas = Image.new("RGB", (W, H), tuple(c["background"]))
            canvas.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
            p.stdin.write(np.asarray(canvas).tobytes())
        total += len(frames)
    p.stdin.close()
    p.wait()
    a, b = CFG["intro"]["S03"]
    assert total == b - a, (total, b - a)  # the edit's S03 slot
    print(f"{OUT}: {total} frames")


if __name__ == "__main__":
    main()
