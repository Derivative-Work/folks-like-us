"""The YouTube thumbnails, under O's thumb cards (takes/o/cards/thumb and thumb_portrait, scripts/o_render_all.sh):
  main   the cold open's porch (song frame 2432: the two raised fingers, the data center behind), composited and graded
         as in the edit but without the screen layer, scaled to 1280x720
  short  the vertical cut's porch (song frame 2430: both hands up), as in the vertical cut without its screen layer,
         at 1080x1920

Output: deliverables/folks_like_us_thumbnail.jpg, deliverables/folks_like_us_shorts_thumbnail.jpg
Usage: .venv/bin/python scripts/thumbnail.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import e_edit as e  # noqa: E402

MAIN, SHORT = 2432, 2430
OUT = Path("deliverables")


def main():
    OUT.mkdir(exist_ok=True)
    pic, is_card = e.song_picture(MAIN, cold=True)
    img = e.finish(pic, is_card, MAIN + 100000, e.overlay("takes/o/cards/thumb/00000.png"))  # the cold open's grain seed
    img.resize((1280, 720), e.Image.LANCZOS).save(OUT / "folks_like_us_thumbnail.jpg", quality=92, optimize=True)
    img = e.finish(e.vertical_picture(SHORT), False, SHORT + 200000, e.overlay("takes/o/cards/thumb_portrait/00000.png"),
                   tuple(e.CFG["vertical"]["size"]))  # the vertical cut's grain seed
    img.save(OUT / "folks_like_us_shorts_thumbnail.jpg", quality=92, optimize=True)
    print(*sorted(OUT.glob("*thumbnail.jpg")))


if __name__ == "__main__":
    main()
