"""Keyframe picks contact sheet [H checkpoint]: the recommended keyframe for every V shot, in shot order.

Reads config/keyframe_picks.json (a file name, or {"file", "flag"} for a pick with a known weakness) and lays out one
card per shot from takes/keyframes/<shot>/<file>, with the flag in orange under it. Vertical shots get their own row.

Usage: .venv/bin/python scripts/picks_sheet.py [out=takes/keyframes/picks_contact_sheet.png]
"""
import json
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "takes/keyframes/picks_contact_sheet.png")
PICKS = json.load(open("config/keyframe_picks.json"))["picks"]
COLS, CARD_W, GAP, TEXT_H = 5, 560, 12, 96
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
BOLD = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)


def card(shot, pick):
    name, flag = (pick["file"], pick["flag"]) if isinstance(pick, dict) else (pick, "")
    im = Image.open(Path("takes/keyframes") / shot / name).convert("RGB")
    w = CARD_W if im.width > im.height else CARD_W // 2
    im = im.resize((w, round(w * im.height / im.width)))
    c = Image.new("RGB", (w, im.height + TEXT_H), (16, 16, 18))
    c.paste(im, (0, 0))
    d = ImageDraw.Draw(c)
    d.text((6, im.height + 6), name.removesuffix(".png"), fill=(255, 255, 255), font=BOLD)
    for i, line in enumerate(textwrap.wrap(flag, 46 if w == CARD_W else 22)[:3]):
        d.text((6, im.height + 36 + 20 * i), line, fill=(255, 160, 40), font=FONT)
    return c


def main():
    cards = [card(s, p) for s, p in PICKS.items()]
    wide = [c for c in cards if c.width == CARD_W]
    tall = [c for c in cards if c.width != CARD_W]
    rows = [wide[i:i + COLS] for i in range(0, len(wide), COLS)] + ([tall] if tall else [])
    width = COLS * (CARD_W + GAP) + GAP
    height = 60 + sum(max(c.height for c in r) + GAP for r in rows) + GAP
    sheet = Image.new("RGB", (width, height), (8, 8, 10))
    ImageDraw.Draw(sheet).text((GAP, 16), f"Keyframe picks for [H]: {len(cards)} V shots (orange: known weakness)",
                               fill=(255, 210, 0), font=BOLD)
    y = 60
    for r in rows:
        x = GAP
        for c in r:
            sheet.paste(c, (x, y))
            x += c.width + GAP
        y += max(c.height for c in r) + GAP
    sheet.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
