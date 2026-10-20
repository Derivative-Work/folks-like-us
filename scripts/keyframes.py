"""Production S: photoreal keyframes for the V shots, from the Blender first frame and the approved sheets.

FLUX.2 [dev] reference editing, the same nodes as ComfyUI's image_flux2_fp8 template: each reference image is scaled
to 1 megapixel, VAE-encoded and chained through ReferenceLatent after FluxGuidance. Reference 1 is the shot's layout
(renders/b/keyframe/<shot>/beauty/<first frame>.png, rendered with render_shot.py --first); the others are the
kept sheets the shot casts (config/keyframes.json). From v3 the sampler also starts from the layout itself (VAE-encoded,
noised to "denoise"), so the camera and geometry hold, and the building sentence follows the layout's building_mask
coverage: none, tiny on the horizon, or large. Outputs: takes/keyframes/<shot>/<shot>_s<seed>.png, plus
takes/keyframes/review_<shot>.png (the layout, each candidate, and each candidate with the layout's depth edges
over it in red, to check that the geometry held). Every generation is a row in log/production_log.md.

Usage: .venv/bin/python scripts/keyframes.py [shot ...] [--seeds 2001,2002] [--denoise 0.85]   (ComfyUI must be running)
       A shot's own "seeds" in the config (new seeds for an unchanged prompt) override the default seeds.
       --denoise overrides the config for a test; its outputs get a _d<NN> suffix.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import comfy_client as cc  # noqa: E402
from stills import CFG as STILLS  # noqa: E402

CFG = json.load(open("config/keyframes.json"))
SHOTS_B = json.load(open("config/shots_b.json"))["shots"]
LAYOUTS = Path("renders/b/keyframe")
OUT = Path("takes/keyframes")
PROMPTS = Path("log/prompts/keyframes")
LOG = Path("log/production_log.md")


def layout(shot):
    meta = json.load(open(LAYOUTS / shot / "shot.json"))
    f = meta["frames_rendered"][0]
    return LAYOUTS / shot / "beauty" / f"{f:05d}.png", LAYOUTS / shot / "depth" / f"{f:05d}.png", meta


def building(shot):
    meta = json.load(open(LAYOUTS / shot / "shot.json"))
    f = meta["frames_rendered"][0]
    pct = 100 * float((np.asarray(Image.open(LAYOUTS / shot / "mask" / f"{f:05d}.png")) > 127).mean())
    b = CFG["building"]
    return b["none"] if pct == 0 else b["tiny"] if pct < b["tiny_below_pct"] else b["large"]


def graph(prompt, ref_names, seed, w, h, prefix, denoise=1.0):
    m = STILLS["model"]
    g = {
        "12": {"class_type": "UNETLoader", "inputs": {"unet_name": m["unet"], "weight_dtype": "default"}},
        "38": {"class_type": "CLIPLoader", "inputs": {"clip_name": m["clip"], "type": "flux2", "device": "default"}},
        "10": {"class_type": "VAELoader", "inputs": {"vae_name": m["vae"]}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["38", 0]}},
        "26": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["6", 0], "guidance": m["guidance"]}},
    }
    cond = ["26", 0]
    for i, name in enumerate(ref_names):
        g[f"ref{i}_load"] = {"class_type": "LoadImage", "inputs": {"image": name}}
        g[f"ref{i}_scale"] = {"class_type": "ImageScaleToTotalPixels",
                              "inputs": {"image": [f"ref{i}_load", 0], "upscale_method": "area", "megapixels": 1.0,
                                         "resolution_steps": 1}}
        g[f"ref{i}_enc"] = {"class_type": "VAEEncode", "inputs": {"pixels": [f"ref{i}_scale", 0], "vae": ["10", 0]}}
        g[f"ref{i}"] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": cond, "latent": [f"ref{i}_enc", 0]}}
        cond = [f"ref{i}", 0]
    g.update({
        "22": {"class_type": "BasicGuider", "inputs": {"model": ["12", 0], "conditioning": cond}},
        "25": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
        "16": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": m["sampler"]}},
        "48": {"class_type": "Flux2Scheduler", "inputs": {"steps": m["steps"], "width": w, "height": h}},
        "47": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "13": {"class_type": "SamplerCustomAdvanced",
               "inputs": {"noise": ["25", 0], "guider": ["22", 0], "sampler": ["16", 0], "sigmas": ["48", 0],
                          "latent_image": ["47", 0]}},
    })
    if denoise < 1.0:  # img2img: start from the layout (reference 1) at full size, on the tail of the schedule
        g.update({
            "init_scale": {"class_type": "ImageScale", "inputs": {"image": ["ref0_load", 0], "upscale_method": "area",
                                                                  "width": w, "height": h, "crop": "center"}},
            "init_enc": {"class_type": "VAEEncode", "inputs": {"pixels": ["init_scale", 0], "vae": ["10", 0]}},
            "split": {"class_type": "SplitSigmasDenoise", "inputs": {"sigmas": ["48", 0], "denoise": denoise}},
        })
        del g["47"]
        g["13"]["inputs"].update({"sigmas": ["split", 1], "latent_image": ["init_enc", 0]})
    g.update({
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["13", 0], "vae": ["10", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": prefix}},
    })
    return g


def depth_edges(depth_png, size):
    d = Image.open(depth_png)
    a = np.asarray(d, dtype=np.float32)
    a = a / a.max() if a.max() > 0 else a
    e = Image.fromarray((a * 255).astype(np.uint8)).resize(size).filter(ImageFilter.FIND_EDGES)
    return e.point(lambda v: 255 if v > 18 else 0)


def review(shot, lay, depth, cands):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    lay_im = Image.open(lay).convert("RGB")
    tw = 760
    th = round(tw * lay_im.height / lay_im.width)
    edges = depth_edges(depth, (tw, th))
    cols = [("layout", lay_im)] + [(f"seed {p.stem.split('_s')[-1]}", Image.open(p).convert("RGB")) for p in cands]
    grid = Image.new("RGB", (len(cols) * (tw + 10) + 10, 2 * th + 110), (16, 16, 18))
    d = ImageDraw.Draw(grid)
    d.text((12, 10), f"{shot}: keyframe candidates (bottom row: layout depth edges in red)", fill=(255, 255, 255),
           font=font)
    for k, (label, im) in enumerate(cols):
        x = 10 + k * (tw + 10)
        small = im.resize((tw, th))
        grid.paste(small, (x, 50))
        over = small.copy()
        over.paste((255, 40, 40), (0, 0), edges)
        grid.paste(over, (x, 60 + th))
        d.text((x + 8, 54), label, fill=(255, 210, 0), font=font)
    out = OUT / f"review_{shot}.png"
    grid.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--seeds")
    ap.add_argument("--denoise", type=float)
    args = ap.parse_args()
    denoise = args.denoise if args.denoise is not None else CFG.get("denoise", 1.0)
    shots = args.shots or list(CFG["shots"])
    PROMPTS.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    uploaded = {}
    rows = []
    for shot in shots:
        spec = CFG["shots"][shot]
        seeds = [int(s) for s in args.seeds.split(",")] if args.seeds else spec.get("seeds", CFG["seeds"])
        lay, depth, meta = layout(shot)
        w, h = CFG["size"]
        if meta["resolution"][1] > meta["resolution"][0]:
            w, h = h, w
        v = spec.get("v", 1)
        prompt = f"{CFG['layout_prefix']} {spec['prompt']} {CFG['style']}"
        if v >= 3:
            prompt = f"{prompt} {building(shot)}"
        if v >= 4 and "patrons" not in SHOTS_B[shot]["cast"]:
            prompt = f"{prompt} {CFG['empty']}"
        stem = shot if v == 1 else f"{shot}_v{v}"
        if args.denoise is not None:
            stem += f"_d{round(args.denoise * 100)}"
        if not all((OUT / shot / f"{stem}_s{seed}.png").exists() for seed in seeds):
            (PROMPTS / f"{stem}.txt").write_text(prompt + "\n")  # only when generating: keeps old prompts true
        refs = [str(lay)] + [CFG["refs"][r] for r in spec["refs"]]
        names = []
        for r in refs:
            if r not in uploaded:
                uploaded[r] = cc.upload_image(r)
            names.append(uploaded[r])
        cands = []
        for seed in seeds:
            dest = OUT / shot / f"{stem}_s{seed}.png"
            if not dest.exists():
                dn = (args.denoise or spec.get("denoise", denoise)) if v >= 3 else 1.0
                outputs, secs = cc.run(graph(prompt, names, seed, w, h, f"folks/kf_{stem}_s{seed}", dn))
                cc.download(outputs["9"]["images"][0], dest)
                rows.append((stem, seed, dn, ", ".join(refs), str(dest), round(secs, 1)))
                print(f"{shot} seed {seed}: {dest} ({secs:.1f} s)")
            cands.append(dest)
        print("review:", review(stem, lay, depth, cands))
    if rows:
        m = STILLS["model"]
        with open(LOG, "a") as f:
            f.write(f"\n## {started} — S: keyframes ({', '.join(shots)})\n\n"
                    f"- **Model:** FLUX.2 [dev] `{m['unet']}`, `{m['clip']}`, `{m['vae']}`; {m['steps']} steps, "
                    f"{m['sampler']}, guidance {m['guidance']}, denoise from the layout per row (v3 and later; 1.0 = none); reference editing (ReferenceLatent, 1 MP per "
                    f"reference), {CFG['size'][0]}×{CFG['size'][1]}.\n"
                    f"- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python "
                    f"scripts/keyframes.py {' '.join(args.shots)}{' --seeds ' + args.seeds if args.seeds else ''}"
                    f"{f' --denoise {args.denoise}' if args.denoise is not None else ''}`\n\n"
                    f"| Shot | Seed | Denoise | Inputs (reference 1 = layout) | Output | Seconds | Status |\n"
                    f"| --- | --- | --- | --- | --- | --- | --- |\n")
            for shot, seed, dn, refs, dest, secs in rows:
                f.write(f"| {shot} | {seed} | {dn} | {refs} | `{dest}` | {secs} | pending [H] |\n")


if __name__ == "__main__":
    main()
