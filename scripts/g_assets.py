"""G: the generated pieces the glitch passes cut in (config/g.json), with FLUX.2 in ComfyUI.

  edit   a frame of an approved take (or a keyframe): a square crop around the subject, upscaled to edit_size, run
         through FLUX.2 img2img with the crop as reference 1 and init, then scaled back to the crop's size.
         Output: takes/g/assets/<name>/f<frame>_s<seed>.png (the crop size; g_pass.py pastes it at "box").
  still  a text-to-image still: takes/g/assets/<name>/<name>_s<seed>.png; with "refs", the reference images are
         chained in as the keyframes are (the approved singer sheet for the S20 TV ads).
Each asset gets a review sheet, takes/g/assets/<name>/review.png (source crop first). Every output is a row in
log/production_log.md.

Usage: .venv/bin/python scripts/g_assets.py [asset ...]   (ComfyUI must be running)
"""
import datetime
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import comfy_client as cc  # noqa: E402
import keyframes  # noqa: E402
import stills  # noqa: E402

CFG = json.load(open("config/g.json"))
OUT = Path("takes/g/assets")
LOG = Path("log/production_log.md")


def frame(source, n):
    """Frame n of a take (0-based), or the image itself."""
    if source.endswith(".png"):
        return Image.open(source).convert("RGB")
    tmp = OUT / "_frame.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", source, "-vf", f"select=eq(n\\,{n})", "-frames:v", "1",
                    str(tmp)], check=True)
    return Image.open(tmp).convert("RGB")


def review(d, cells):
    w = 300
    sheet = Image.new("RGB", (w * len(cells), w + 24), (12, 12, 14))
    for i, (label, im) in enumerate(cells):
        sheet.paste(im.resize((w, round(w * im.height / im.width))).crop((0, 0, w, w)), (i * w, 24))
        ImageDraw.Draw(sheet).text((i * w + 4, 4), label, fill=(255, 210, 0))
    sheet.save(d / "review.png")


def main():
    names = sys.argv[1:] or list(CFG["assets"])
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    rows = []
    for name in names:
        a = CFG["assets"][name]
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        cells = []
        if a["kind"] == "still":
            w, h = a["size"]
            for seed in a["seeds"]:
                out = d / f"{name}_s{seed}.png"
                if a.get("refs"):  # text-to-image with reference images (an approved character sheet), as keyframes
                    refs = [cc.upload_image(Path(r)) for r in a["refs"]]
                    g = keyframes.graph(a["prompt"], refs, seed, w, h, f"folks/g_{name}_s{seed}")
                else:
                    g = stills.graph(a["prompt"], seed, w, h, f"folks/g_{name}_s{seed}")
                outputs, secs = cc.run(g)
                cc.download(outputs["9"]["images"][0], out)
                rows.append((name, "-", seed, "-", str(out), round(secs, 1)))
                cells.append((f"s{seed}", Image.open(out)))
        else:
            n = CFG["edit_size"]
            for f in a["frames"]:
                crop = frame(a["source"], f).crop(a["box"])
                src = d / f"f{f}_src.png"
                crop.resize((n, n), Image.LANCZOS).save(src)
                cells.append((f"f{f} source", crop))
                ref = cc.upload_image(src)
                for seed in a["seeds"]:
                    out = d / f"f{f}_s{seed}.png"
                    g = keyframes.graph(a["prompt"], [ref], seed, n, n, f"folks/g_{name}_f{f}_s{seed}", a["denoise"])
                    outputs, secs = cc.run(g)
                    cc.download(outputs["9"]["images"][0], out)
                    Image.open(out).resize(crop.size, Image.LANCZOS).save(out)
                    rows.append((name, f, seed, a["denoise"], str(out), round(secs, 1)))
                    cells.append((f"f{f} s{seed}", Image.open(out)))
                    print(f"{name} f{f} s{seed}: {out} ({secs:.0f} s)", flush=True)
        review(d, cells)
        print(f"review: {d / 'review.png'}")
    with open(LOG, "a") as fh:
        fh.write(f"\n## {started} — G: generated pieces for the glitch passes ({', '.join(names)})\n\n"
                 f"- **Model:** FLUX.2 [dev] fp8 (`config/stills.json` model), img2img from a 1024 px crop (edits) or "
                 f"text-to-image (stills). **Prompts, boxes, frames:** `config/g.json`. **Command:** "
                 f"`.venv/bin/python scripts/g_assets.py {' '.join(sys.argv[1:])}`\n\n"
                 f"| Asset | Frame | Seed | Denoise | Output | Seconds | Status |\n| --- | --- | --- | --- | --- | --- | --- |\n")
        for r in rows:
            fh.write(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | `{r[4]}` | {r[5]} | pending |\n")


if __name__ == "__main__":
    main()
