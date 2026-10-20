"""Production L: lip-sync the singer on each L shot's approved V take with LatentSync 1.6 (config/l.json).

LatentSync re-generates only the lower face of existing footage from the audio, so the V take stays the take. It
runs from ByteDance's repo in its own venv (~/LatentSync, scripts/setup_env.sh), not in ComfyUI: its dependencies
would replace packages ComfyUI needs (log/decisions.md).

Per shot and seed:
  1. A crop that follows the singer's face (YuNet boxes from l_faces.py, smoothed), `crop_scale` face heights
     square, scaled to 512 px: LatentSync skips faces under 50x80 px (S12 starts far away) and works at 512 anyway.
  2. LatentSync works at 25 fps. The crop's frames are labelled 25 fps and the vocal is sped up by 25/24 to match,
     so every frame keeps its own audio and no frame is dropped or interpolated.
  3. The synced crop is scaled back and pasted onto the V take through a feathered ellipse around the face, so
     outside the face every pixel is the approved take.

Outputs: takes/l/<shot>/<shot>_s<seed>.mp4 (picture only, the shot's frames) and _audio.mp4 (with the master, for
review); the crop, the vocal and LatentSync's output in takes/l/<shot>/s<seed>/. One log row per take.

Extra shots (config/l.json "extra": S10, S21, S30, S30v) have no V take of their own: `--prepare` builds each one's
source clip from an approved take, l_faces.py tracks it, and this script syncs it like an L shot.

Usage: .venv/bin/python scripts/l_batch.py [shot ...] [--seeds 1,2] [--prepare]
       (run l_faces.py first; free ComfyUI's GPU)
"""
import argparse
import datetime
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from v_batch import FPS, TIMES, span  # noqa: E402

CFG = json.load(open("config/l.json"))
OUT = Path("takes/l")
LOG = Path("log/production_log.md")
MASTER = "audio/master/folks_like_us_master_nofallback.wav"
LS_DIR = Path.home() / "LatentSync"
LS_FPS = 25
CROP = 512


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def smooth(values, k):
    """Moving average over k frames (edges padded), so the crop doesn't jitter with the detector."""
    v = np.asarray(values, dtype=np.float64)
    pad = np.pad(v, ((k // 2, k // 2), (0, 0)), mode="edge")
    return np.stack([pad[i:i + len(v)] for i in range(k)]).mean(0)


def crops(faces):
    """Per frame (cx, cy, side): a square around the face, `crop_scale` face heights, centred a little below the
    face centre to take in the chin and jaw."""
    boxes = list(faces)
    for i, b in enumerate(boxes):  # fill missed detections from the nearest found frame
        if b is None:
            boxes[i] = next(boxes[j] for d in range(1, len(boxes)) for j in (i - d, i + d)
                            if 0 <= j < len(boxes) and boxes[j] is not None)
    c = np.array([[b[0] + b[2] / 2, b[1] + b[3] * 0.6, b[3]] for b in boxes])
    c = smooth(c, CFG["smooth"])
    return [(x, y, h * CFG["crop_scale"]) for x, y, h in c]


def cut(frame, cx, cy, side):
    """The square crop (edge-padded where it leaves the frame), scaled to CROP px."""
    a = np.asarray(frame)
    h, w = a.shape[:2]
    s = int(round(side))
    x0, y0 = int(round(cx - s / 2)), int(round(cy - s / 2))
    xs = np.clip(np.arange(x0, x0 + s), 0, w - 1)
    ys = np.clip(np.arange(y0, y0 + s), 0, h - 1)
    return Image.fromarray(a[ys][:, xs]).resize((CROP, CROP), Image.LANCZOS), (x0, y0, s)


def ellipse(s):
    """The paste mask in a crop of side s: an ellipse over the face's lower two thirds, feathered."""
    m = Image.new("L", (s, s), 0)
    ImageDraw.Draw(m).ellipse([s * 0.22, s * 0.18, s * 0.78, s * 0.86], fill=255)
    return m.filter(ImageFilter.GaussianBlur(s * 0.05))


def paste(frame, synced, box):
    x0, y0, s = box
    out = frame.copy()
    out.paste(synced.resize((s, s), Image.LANCZOS), (x0, y0), ellipse(s))
    return out


HEADER = [False]
STARTED = datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def log_row(shot, seed, n, synced, take, out, secs):
    """Append the take's row right away, so a run that is stopped part way loses no log entries."""
    with open(LOG, "a") as f:
        if not HEADER[0]:
            HEADER[0] = True
            commit = subprocess.run(["git", "-C", str(LS_DIR), "rev-parse", "--short", "HEAD"], capture_output=True,
                                    text=True).stdout.strip()
            f.write(f"\n## {STARTED} — L: lip-sync with LatentSync 1.6 ({' '.join(sys.argv[1:]) or 'all L shots'})\n\n"
                    f"- **Model:** LatentSync 1.6 (`ByteDance/LatentSync-1.6` `latentsync_unet.pt`, code "
                    f"`bytedance/LatentSync` {commit}), {CFG['steps']} steps, guidance {CFG['guidance']}, DeepCache.\n"
                    f"- **Inputs:** the V pick (`config/v_picks.json`), `{CFG['vocal']}`; a face crop of "
                    f"{CFG['crop_scale']} face heights from `takes/l/<shot>/faces.json` (`scripts/l_faces.py`), "
                    f"512 px, 24 fps frames labelled 25 fps with the vocal sped up 25/24. Pasted back through a "
                    f"feathered ellipse around the face. **Command:** `.venv/bin/python scripts/l_batch.py "
                    f"{' '.join(sys.argv[1:])}`\n\n"
                    f"| Shot | Seed | Frames | Synced | Input | Output | Seconds | Status |\n"
                    f"| --- | --- | --- | --- | --- | --- | --- | --- |\n")
        f.write(f"| {shot} | {seed} | {n} | {synced} | `{take}` | `{out}` | {secs} | pending [H] |\n")


def shot_span(shot):
    """(s0, s1, vocal start in s): an L shot's own frames, or an "extra" shot's (config/l.json "extra")."""
    x = CFG.get("extra", {}).get(shot)
    if not x:
        s0, s1 = span(shot)
        return s0, s1, s0 / FPS
    t = TIMES[x.get("time", shot)]
    return t["start_frame"], t["end_frame"], x.get("vocal_at", t["start_frame"] / FPS)


def prepare_extra(shot):
    """An extra shot's source clip, takes/l/<shot>/source.mp4: frames of an approved take ("from", from "start"), or
    one frame of it ("hold") repeated for the shot's length."""
    x = CFG["extra"][shot]
    s0, s1, _ = shot_span(shot)
    out = OUT / shot / "source.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    if "hold" in x:
        vf = f"select=eq(n\\,{x['hold']}),loop={s1 - s0 - 1}:1:0,setpts=N/{FPS}/TB"
    else:
        vf = f"trim=start_frame={x.get('start', 0)}:end_frame={x.get('start', 0) + s1 - s0},setpts=N/{FPS}/TB"
    ffmpeg("-i", x["from"], "-vf", vf, "-frames:v", str(s1 - s0), "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p",
           str(out))
    return out


def gen(shots, seeds):
    for shot in shots:
        faces = json.load(open(OUT / shot / "faces.json"))
        s0, s1, vocal_at = shot_span(shot)
        n = s1 - s0
        d = OUT / shot
        for seed in seeds:
            final = d / f"{shot}_s{seed}.mp4"
            if final.exists():
                continue
            work = d / f"s{seed}"
            shutil.rmtree(work, ignore_errors=True)
            for sub in ("v", "crop", "out"):
                (work / sub).mkdir(parents=True)
            ffmpeg("-i", faces["take"], "-frames:v", str(n), str(work / "v" / "%05d.png"))
            frames = sorted((work / "v").glob("*.png"))
            boxes = []
            for f, (cx, cy, side) in zip(frames, crops(faces["faces"][:n])):
                im, box = cut(Image.open(f).convert("RGB"), cx, cy, side)
                im.save(work / "crop" / f.name)
                boxes.append(box)
            crop, vocal, synced = work / "crop.mp4", work / "vocal.wav", work / "synced.mp4"
            ffmpeg("-framerate", str(LS_FPS), "-i", str(work / "crop" / "%05d.png"), "-c:v", "libx264", "-crf", "10",
                   "-pix_fmt", "yuv420p", str(crop))
            ffmpeg("-ss", f"{vocal_at:.4f}", "-t", f"{n / FPS:.4f}", "-i", CFG["vocal"],
                   "-af", f"atempo={LS_FPS / FPS:.6f}", "-ac", "1", "-ar", "16000", str(vocal))
            cmd = [str(LS_DIR / ".venv/bin/python"), "-m", "scripts.inference",
                   "--unet_config_path", "configs/unet/stage2_512.yaml",
                   "--inference_ckpt_path", "checkpoints/latentsync_unet.pt",
                   "--inference_steps", str(CFG["steps"]), "--guidance_scale", str(CFG["guidance"]),
                   "--enable_deepcache", "--seed", str(seed), "--temp_dir", str((work / "tmp").resolve()),
                   "--video_path", str(crop.resolve()), "--audio_path", str(vocal.resolve()),
                   "--video_out_path", str(synced.resolve())]
            t0 = time.time()
            r = subprocess.run(cmd, cwd=LS_DIR, capture_output=True, text=True)
            secs = round(time.time() - t0, 1)
            if r.returncode:
                print(r.stdout[-2000:], r.stderr[-4000:])
                raise SystemExit(f"{shot} seed {seed}: LatentSync failed")
            ffmpeg("-i", str(synced), str(work / "out" / "%05d.png"))
            out = sorted((work / "out").glob("*.png"))
            for i, f in enumerate(frames):
                if i < len(out):  # LatentSync can stop a frame short of the audio's end; those frames stay V
                    paste(Image.open(f).convert("RGB"), Image.open(out[i]).convert("RGB"), boxes[i]).save(f)
            ffmpeg("-framerate", str(FPS), "-i", str(work / "v" / "%05d.png"), "-frames:v", str(n), "-c:v", "libx264",
                   "-crf", "14", "-pix_fmt", "yuv420p", str(final))
            ffmpeg("-i", str(final), "-ss", f"{s0 / FPS:.4f}", "-t", f"{n / FPS:.4f}", "-i", MASTER, "-map", "0:v",
                   "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(d / f"{shot}_s{seed}_audio.mp4"))
            log_row(shot, seed, n, len(out), faces["take"], str(final), secs)
            print(f"{shot} seed {seed}: {final} ({n} frames, {len(out)} synced, {secs} s)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--seeds")
    ap.add_argument("--prepare", action="store_true", help="build the extra shots' source clips and stop")
    a = ap.parse_args()
    if a.prepare:
        for shot in a.shots or list(CFG.get("extra", {})):
            if shot != "note":
                print(prepare_extra(shot))
        return
    gen(a.shots or list(CFG["shots"]), [int(s) for s in a.seeds.split(",")] if a.seeds else CFG["seeds"])


if __name__ == "__main__":
    main()
