"""V review grids [H checkpoint]: for each V shot, four evenly spaced frames of every take (one row per seed),
labelled with shot, seed and frame. Writes takes/v/review_<shot>.png and pages of several shots,
takes/v/review_page<N>.png.

Usage: .venv/bin/python scripts/v_review.py [shot ...] [--per-page 4]
"""
import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

CFG = json.load(open("config/v.json"))
OUT = Path("takes/v")
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
TW = 420


def frames(take, k=4):
    n = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-show_entries", "stream=nb_read_frames",
                            "-of", "csv=p=0", str(take)], capture_output=True, text=True).stdout)
    idx = sorted({round(i * (n - 1) / (k - 1)) for i in range(k)})
    sel = "+".join(f"eq(n\\,{i})" for i in idx)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(take), "-vf", f"select='{sel}'", "-vsync", "0",
                          "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
    ims, i = [], 0
    while (j := raw.find(b"\x89PNG", i + 1)) != -1 or i < len(raw):
        chunk = raw[i:j if j != -1 else len(raw)]
        from io import BytesIO
        ims.append(Image.open(BytesIO(chunk)).convert("RGB"))
        if j == -1:
            break
        i = j
    return list(zip(idx, ims))


def shot_grid(shot):
    takes = sorted(OUT.glob(f"{shot}/{shot}_s[0-9].mp4"))
    rows = []
    for t in takes:
        fs = frames(t)
        w, h = fs[0][1].size
        th = round(TW * h / w) if w > h else round(TW * 1.0)
        tw = TW if w > h else round(th * w / h)
        row = Image.new("RGB", (len(fs) * (tw + 6), th + 30), (12, 12, 14))
        d = ImageDraw.Draw(row)
        d.text((4, 4), f"{shot}  seed {t.stem.split('_s')[-1]}", fill=(255, 210, 0), font=FONT)
        for k, (n, im) in enumerate(fs):
            row.paste(im.resize((tw, th)), (k * (tw + 6), 30))
            d.text((k * (tw + 6) + tw - 70, 4), f"f{n}", fill=(200, 200, 200), font=FONT)
        rows.append(row)
    g = Image.new("RGB", (max(r.width for r in rows), sum(r.height + 6 for r in rows)), (0, 0, 0))
    y = 0
    for r in rows:
        g.paste(r, (0, y))
        y += r.height + 6
    g.save(OUT / f"review_{shot}.png")
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--per-page", type=int, default=4)
    a = ap.parse_args()
    shots = a.shots or list(CFG["shots"])
    grids = [shot_grid(s) for s in shots]
    for p in range(0, len(grids), a.per_page):
        gs = grids[p:p + a.per_page]
        page = Image.new("RGB", (max(g.width for g in gs), sum(g.height + 20 for g in gs)), (40, 40, 44))
        y = 0
        for g in gs:
            page.paste(g, (0, y))
            y += g.height + 20
        out = OUT / f"review_page{p // a.per_page + 1}.png"
        page.save(out)
        print(out, ", ".join(shots[p:p + a.per_page]))


if __name__ == "__main__":
    main()
