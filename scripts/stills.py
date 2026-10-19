"""Pre-production step 6 [S]: reference stills with FLUX.2 [dev] via ComfyUI, for [H] to approve.

For each item in config/stills.json and each seed: build the FLUX.2 text-to-image graph (the same nodes as ComfyUI's
image_flux2_fp8 template: UNet + Mistral text encoder, FluxGuidance, BasicGuider, Flux2Scheduler, euler,
SamplerCustomAdvanced), render, and save takes/stills/<item>/<item>_s<seed>.png. Every generation is appended to
log/production_log.md as one table row (item, seed, output, seconds, status), and each prompt is saved to
log/prompts/stills/<item>.txt (<item>_v<N>.txt for a revised prompt; earlier versions are kept). A 2x2 review grid per item goes to takes/stills/review_<item>.png.

Usage: .venv/bin/python scripts/stills.py [item ...] [--seeds 1001,1002]   (ComfyUI must be running)
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import comfy_client as cc  # noqa: E402

CFG = json.load(open("config/stills.json"))
OUT = Path("takes/stills")
PROMPTS = Path("log/prompts/stills")
LOG = Path("log/production_log.md")


def graph(prompt, seed, w, h, prefix):
    m = CFG["model"]
    return {
        "12": {"class_type": "UNETLoader", "inputs": {"unet_name": m["unet"], "weight_dtype": "default"}},
        "38": {"class_type": "CLIPLoader", "inputs": {"clip_name": m["clip"], "type": "flux2", "device": "default"}},
        "10": {"class_type": "VAELoader", "inputs": {"vae_name": m["vae"]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["38", 0]}},
        "26": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["6", 0], "guidance": m["guidance"]}},
        "22": {"class_type": "BasicGuider", "inputs": {"model": ["12", 0], "conditioning": ["26", 0]}},
        "25": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "16": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": m["sampler"]}},
        "48": {"class_type": "Flux2Scheduler", "inputs": {"steps": m["steps"], "width": w, "height": h}},
        "47": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "13": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["25", 0], "guider": ["22", 0], "sampler": ["16", 0], "sigmas": ["48", 0],
                          "latent_image": ["47", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["10", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    }


def review_grid(item, paths):
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = 960, round(960 * ims[0].height / ims[0].width)
    grid = Image.new("RGB", (2 * w + 30, 2 * h + 90), (16, 16, 18))
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    d = ImageDraw.Draw(grid)
    d.text((12, 12), f"{item}: pick one", fill=(255, 255, 255), font=font)
    for k, (p, im) in enumerate(zip(paths, ims)):
        x, y = 10 + (k % 2) * (w + 10), 60 + (k // 2) * (h + 10)
        grid.paste(im.resize((w, h)), (x, y))
        d.rectangle((x, y, x + 260, y + 40), fill=(0, 0, 0))
        d.text((x + 8, y + 6), f"{chr(65 + k)}  seed {p.stem.split('_s')[-1]}", fill=(255, 210, 0), font=font)
    out = OUT / f"review_{item}.png"
    grid.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("items", nargs="*")
    ap.add_argument("--seeds")
    args = ap.parse_args()
    items = args.items or list(CFG["items"])
    seeds = [int(s) for s in args.seeds.split(",")] if args.seeds else CFG["seeds"]
    m = CFG["model"]
    rows = []
    PROMPTS.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    for item in items:
        spec = CFG["items"][item]
        stem = item if spec.get("v", 1) == 1 else f"{item}_v{spec['v']}"
        (PROMPTS / f"{stem}.txt").write_text(spec["prompt"] + "\n")
        w, h = spec["size"]
        paths = []
        for seed in (spec.get("seeds") if not args.seeds and "seeds" in spec else seeds):
            dest = OUT / item / f"{stem}_s{seed}.png"
            if dest.exists():
                print(f"{dest} exists, skipping")
                paths.append(dest)
                continue
            outputs, secs = cc.run(graph(spec["prompt"], seed, w, h, f"folks/{stem}_s{seed}"))
            img = outputs["9"]["images"][0]
            cc.download(img, dest)
            paths.append(dest)
            rows.append((stem, seed, str(dest), round(secs, 1)))
            print(f"{item} seed {seed}: {dest} ({secs:.1f} s)")
        if len(paths) >= 2:
            print("review:", review_grid(stem, paths[:4]))
    if rows:
        with open(LOG, "a") as f:
            f.write(f"\n## {started} — S: reference stills ({', '.join(items)})\n\n"
                    f"- **Model:** FLUX.2 [dev] `{m['unet']}`, text encoder `{m['clip']}`, VAE `{m['vae']}`; "
                    f"{m['steps']} steps, {m['sampler']}, guidance {m['guidance']}; ComfyUI "
                    f"(`scripts/stills.py`, graph as the `image_flux2_fp8` template, text-to-image).\n"
                    f"- **Prompts:** `log/prompts/stills/<item>.txt`. **Inputs:** none (text only).\n"
                    f"- **Command:** `.venv/bin/python scripts/stills.py {' '.join(args.items)}"
                    f"{' --seeds ' + args.seeds if args.seeds else ''}`\n\n"
                    f"| Item | Seed | Output | Seconds | Status |\n| --- | --- | --- | --- | --- |\n")
            for item, seed, dest, secs in rows:
                f.write(f"| {item} | {seed} | `{dest}` | {secs} | pending [H] |\n")


if __name__ == "__main__":
    main()
