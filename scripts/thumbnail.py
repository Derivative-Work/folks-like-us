"""The YouTube thumbnail: the cold open's porch (song frame FRAME: the two raised fingers, the data center behind),
composited and graded as in the edit but without the screen layer, under O's thumb card (takes/o/cards/thumb,
scripts/o_render_all.sh), scaled to 1280x720.

Output: deliverables/folks_like_us_thumbnail.jpg
Usage: .venv/bin/python scripts/thumbnail.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import e_edit as e  # noqa: E402

FRAME = 2432
OUT = Path("deliverables/folks_like_us_thumbnail.jpg")


def main():
    pic, is_card = e.song_picture(FRAME, cold=True)
    img = e.finish(pic, is_card, FRAME + 100000, e.overlay("takes/o/cards/thumb/00000.png"))  # the cold open's grain seed
    OUT.parent.mkdir(exist_ok=True)
    img.resize((1280, 720), e.Image.LANCZOS).save(OUT, quality=92, optimize=True)
    print(OUT)


if __name__ == "__main__":
    main()
