"""Blender contact sheet [H checkpoint]: every B shot's camera, building stage and continuity parameters.

Reads the stills render_shot.py wrote (<dir>/<shot>/{beauty,depth,mask}/*.png and shot.json) and lays out one card
per shot: the beauty frame, small depth and mask insets, and the shot's camera, stage, lights and gauge.

Usage: .venv/bin/python scripts/contact_sheet.py [dir=renders/b/contact] [out=renders/b/contact_sheet.png]
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "renders/b/contact")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "renders/b/contact_sheet.png")
ORDER = json.load(open("config/shots_b.json"))["shots"]
TIMES = json.load(open("timing/shot_times.json"))["shots"]
CARD_W, THUMB_H = 640, 360
TEXT_H = 150
COLS = 4


def font(size):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSans.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default()


def card(sid):
    d = SRC / sid
    meta = json.load(open(d / "shot.json"))
    f = meta["frames_rendered"][0]
    beauty = Image.open(d / "beauty" / f"{f:05d}.png").convert("RGB")
    vertical = beauty.height > beauty.width
    img = Image.new("RGB", (CARD_W, THUMB_H + TEXT_H), (24, 24, 26))
    if vertical:
        b = beauty.resize((round(THUMB_H * beauty.width / beauty.height), THUMB_H))
        img.paste(b, (0, 0))
        inset_x = b.width + 8
    else:
        img.paste(beauty.resize((CARD_W, THUMB_H)), (0, 0))
        inset_x = None
    iw = 150
    for k, kind in enumerate(("depth", "mask")):
        p = Image.open(d / kind / f"{f:05d}.png")
        p = p.point(lambda v: v / 256) if p.mode.startswith("I") else p
        p = p.convert("L").convert("RGB")
        ih = round(iw * p.height / p.width)
        p = p.resize((iw, ih))
        if inset_x is not None:
            x, y = inset_x, 8 + k * (ih + 22)
        else:
            x, y = CARD_W - (2 - k) * (iw + 6), THUMB_H - ih - 6
        img.paste(p, (x, y))
        ImageDraw.Draw(img).text((x + 3, y + 2), kind, fill=(255, 210, 0), font=font(13))
    c = meta["continuity"]
    cam = meta["camera"]
    t = TIMES[meta["time"]]
    lines = [
        f"{sid}  {t['start']:.2f}-{t['end']:.2f} s  frame {f}  {meta['section']}  stage {meta['stage']}",
        f"cam {fmt(cam['cam'])} -> {fmt(cam['target'])}  {cam['lens']} mm f/{cam['fstop']}  {move(cam['move'])}",
        f"sun {c['sun']}  flood {c['flood']}  wash {c['building_wash']}  led {c['led']}  gauge {c['gauge']}"
        f"  cranes {'on' if c['cranes'] else 'off'}",
        f"practicals {json.dumps(c['practicals']).replace(chr(34), '')}",
        f"cast: {', '.join(meta['cast']) or '-'}   text: {', '.join(meta['text_surfaces'][:6]) or '-'}"
        + (" ..." if len(meta["text_surfaces"]) > 6 else ""),
        meta.get("what") or "",
    ]
    dr = ImageDraw.Draw(img)
    for k, line in enumerate(lines):
        dr.text((8, THUMB_H + 6 + k * 23), line[:92], fill=(235, 235, 235) if k else (255, 210, 0),
                font=font(15 if k == 0 else 13))
    return img


def fmt(v):
    return "(" + ", ".join(f"{x:g}" for x in v) + ")" if v else "-"


def move(m):
    if not m:
        return "static"
    return ", ".join(f"{k} {v if not isinstance(v, list) else fmt(v)}" for k, v in m.items())


def main():
    shots = [s for s in ORDER if (SRC / s / "shot.json").exists()]
    cards = [card(s) for s in shots]
    rows = (len(cards) + COLS - 1) // COLS
    W, H = COLS * (CARD_W + 10) + 10, rows * (THUMB_H + TEXT_H + 10) + 70
    sheet = Image.new("RGB", (W, H), (10, 10, 12))
    dr = ImageDraw.Draw(sheet)
    dr.text((14, 18), "Folks Like Us: Blender contact sheet (set kit, step 5). Middle frame of each B shot.",
            fill=(255, 255, 255), font=font(26))
    for i, c in enumerate(cards):
        sheet.paste(c, (10 + (i % COLS) * (CARD_W + 10), 70 + (i // COLS) * (THUMB_H + TEXT_H + 10)))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUT)
    print(f"{OUT}: {len(cards)} shots ({', '.join(shots)})")


if __name__ == "__main__":
    main()
