"""S33 (G): the copy-of-a-copy decay. Each generation is the one before, re-encoded lossily (downscaled, heavily
compressed, scaled back up) and then sent through a low-strength LTX-2.3 pass with the shot's V prompt, so every
generation drifts further from the approved take (config/g.json "decay").

Generation 0 is S33's approved V take with its clips' handles (177 frames, so each window is 8n+1). LTX windows are
config "windows" ([start, length]), crossfaded over their overlap. g_pass.py ramps through the generations over F3
and composites the building back sharp through its mask pass.
Outputs: takes/g/S33/gen<k>/NNNNN.png and gen<k>.mp4. One log row per generation.

Usage: .venv/bin/python scripts/g_decay.py [--from K]   (ComfyUI must be running)
"""
import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import comfy_client as cc  # noqa: E402
from ltx_v import NEGATIVE  # noqa: E402
from v_batch import FPS, clip_plan, join, span  # noqa: E402

CFG = json.load(open("config/g.json"))["decay"]
V = json.load(open("config/v.json"))
PICK = json.load(open("config/v_picks.json"))["picks"]["S33"]
OUT = Path("takes/g/S33")
LOG = Path("log/production_log.md")
CKPT = "ltx-2.3-22b-distilled-fp8.safetensors"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def graph(video, length, prompt, seed, denoise, prefix):
    """Encode the clip, attach an empty audio latent (as V does), and re-denoise it at `denoise`."""
    w, h = V["size"]
    return {
        "ckpt": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "clip": {"class_type": "LTXAVTextEncoderLoader",
                 "inputs": {"text_encoder": "gemma_3_12B_it_fp4_mixed.safetensors", "ckpt_name": CKPT,
                            "device": "default"}},
        "avae": {"class_type": "LTXVAudioVAELoader", "inputs": {"ckpt_name": CKPT}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["clip", 0]}},
        "neg": {"class_type": "CLIPTextEncode", "inputs": {"text": NEGATIVE, "clip": ["clip", 0]}},
        "cond": {"class_type": "LTXVConditioning",
                 "inputs": {"positive": ["pos", 0], "negative": ["neg", 0], "frame_rate": FPS}},
        "vid": {"class_type": "LoadVideo", "inputs": {"file": video}},
        "frames": {"class_type": "GetVideoComponents", "inputs": {"video": ["vid", 0]}},
        "venc": {"class_type": "VAEEncode", "inputs": {"pixels": ["frames", 0], "vae": ["ckpt", 2]}},
        "aud": {"class_type": "LTXVEmptyLatentAudio", "inputs": {"frames_number": length, "frame_rate": FPS,
                                                                 "batch_size": 1, "audio_vae": ["avae", 0]}},
        "av": {"class_type": "LTXVConcatAVLatent", "inputs": {"video_latent": ["venc", 0], "audio_latent": ["aud", 0]}},
        "sample": {"class_type": "KSampler", "inputs": {"seed": seed, "steps": 8, "cfg": 1,
                                                        "sampler_name": "euler_ancestral",
                                                        "scheduler": "linear_quadratic", "denoise": denoise,
                                                        "model": ["ckpt", 0], "positive": ["cond", 0],
                                                        "negative": ["cond", 1], "latent_image": ["av", 0]}},
        "sep": {"class_type": "LTXVSeparateAVLatent", "inputs": {"av_latent": ["sample", 0]}},
        "dec": {"class_type": "VAEDecodeTiled", "inputs": {"samples": ["sep", 0], "vae": ["ckpt", 2], "tile_size": 768,
                                                           "overlap": 64, "temporal_size": 4096,
                                                           "temporal_overlap": 4}},
        "save": {"class_type": "SaveImage", "inputs": {"images": ["dec", 0], "filename_prefix": prefix}},
    }


def gen0():
    """The approved take with its clips' handles, as frames."""
    d = OUT / "gen0"
    if d.exists():
        return sorted(d.glob("*.png"))
    d.mkdir(parents=True)
    s0, s1 = span("S33")
    plan = clip_plan(s1 - s0)
    take = Path("takes/v/S33") / PICK
    full = OUT / "gen0.mp4"
    join([take.with_name(f"{take.stem}_c{k}.mp4") for k in range(len(plan))], sum(plan) - (len(plan) - 1), full)
    ffmpeg("-i", str(full), str(d / "%05d.png"))
    return sorted(d.glob("*.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="start", type=int, default=1)
    ap.add_argument("--to", type=int, help="last generation (default: config)")
    ap.add_argument("--denoise", type=float, help="override the config, for a test")
    a = ap.parse_args()
    if a.denoise is not None:
        CFG["denoise"] = a.denoise
    prompt = f"{V['shots']['S33']} {V['style']}"
    w, h = V["size"]
    prev = gen0() if a.start == 1 else sorted((OUT / f"gen{a.start - 1}").glob("*.png"))
    n = len(prev)
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    rows = []
    for k in range(a.start, (a.to or CFG["generations"]) + 1):
        d = OUT / f"gen{k}"
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir(parents=True)
        lossy = OUT / f"gen{k}_lossy.mp4"  # the copy of a copy: half size, heavy compression, back to full size
        lw, lh = w * CFG["lossy_scale"] // 100 // 2 * 2, h * CFG["lossy_scale"] // 100 // 2 * 2
        ffmpeg("-framerate", str(FPS), "-start_number", "1", "-i", str(prev[0].parent / "%05d.png"),
               "-vf", f"scale={lw}:{lh}:flags=bilinear", "-c:v", "libx264", "-crf", str(CFG["lossy_crf"]),
               "-pix_fmt", "yuv420p", str(lossy))
        frames = np.zeros((n, h, w, 3), np.float32)
        weight = np.zeros((n, 1, 1, 1), np.float32)
        secs_total = 0.0
        for i, (start, length) in enumerate(CFG["windows"]):
            clip = OUT / f"gen{k}_w{i}.mp4"
            ffmpeg("-i", str(lossy), "-vf", f"scale={w}:{h}:flags=bicubic,trim=start_frame={start}:end_frame="
                   f"{start + length},setpts=PTS-STARTPTS", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
                   str(clip))
            g = graph(cc.upload_image(clip), length, prompt, CFG["seed"] + k, CFG["denoise"], f"folks/g_S33_gen{k}_w{i}")
            outputs, secs = cc.run(g, timeout=7200)
            secs_total += secs
            tmp = OUT / f"gen{k}_w{i}"
            shutil.rmtree(tmp, ignore_errors=True)
            tmp.mkdir()
            for j, im in enumerate(outputs["save"]["images"]):
                cc.download(im, tmp / f"{j:05d}.png")
            # Linear crossfade weights over the overlap with the other window.
            ramp = np.ones(length, np.float32)
            ov = CFG["overlap"]
            if i > 0:
                ramp[:ov] = np.linspace(0, 1, ov + 2)[1:-1]
            if i < len(CFG["windows"]) - 1:
                ramp[-ov:] = np.linspace(1, 0, ov + 2)[1:-1]
            for j in range(length):
                frames[start + j] += ramp[j] * np.asarray(Image.open(tmp / f"{j:05d}.png").convert("RGB"), np.float32)
                weight[start + j] += ramp[j]
            shutil.rmtree(tmp)
        out = (frames / weight).round().clip(0, 255).astype(np.uint8)
        for j in range(n):
            Image.fromarray(out[j]).save(d / f"{j + 1:05d}.png")
        ffmpeg("-framerate", str(FPS), "-i", str(d / "%05d.png"), "-c:v", "libx264", "-crf", "16", "-pix_fmt",
               "yuv420p", str(OUT / f"gen{k}.mp4"))
        rows.append((k, round(secs_total, 1)))
        print(f"gen{k}: {OUT / f'gen{k}.mp4'} ({secs_total:.0f} s)", flush=True)
        prev = sorted(d.glob("*.png"))
    with open(LOG, "a") as fh:
        fh.write(f"\n## {started} — G: S33 decay generations\n\n"
                 f"- **Model:** LTX-2.3 22B distilled fp8, Gemma 3 12B fp4; video encoded and re-denoised at "
                 f"{CFG['denoise']} (KSampler, 8 steps linear_quadratic, euler_ancestral, cfg 1, seed {CFG['seed']}+k), "
                 f"no control. Each generation starts from the one before, re-encoded at {CFG['lossy_scale']}% size, "
                 f"x264 crf {CFG['lossy_crf']}. Windows {CFG['windows']}, crossfaded over {CFG['overlap']} frames.\n"
                 f"- **Input:** gen0 = `takes/v/S33/{PICK}` with its clips' handles. **Prompt:** S33's V prompt + style "
                 f"(`config/v.json`). **Command:** `.venv/bin/python scripts/g_decay.py`\n\n"
                 f"| Generation | Output | Seconds | Status |\n| --- | --- | --- | --- |\n")
        for k, secs in rows:
            fh.write(f"| {k} | `takes/g/S33/gen{k}.mp4` | {secs} | pending |\n")


if __name__ == "__main__":
    main()
