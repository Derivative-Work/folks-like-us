"""Production V: every V shot as LTX-2.3 video over its Blender depth pass, starting from its approved keyframe.

Two steps, never at the same time (style/vram_plan.md):
  plates  Blender renders each shot's frames at the V size into renders/b/v_plates/<shot>/ (all passes; V uses depth,
          O and G use the rest). A shot gets its own frames plus handles up to the clip plan's length.
  gen     ComfyUI generates the takes: takes/v/<shot>/<shot>_s<seed>.mp4, trimmed to the shot's own frames.

Clip plan: LTX takes 8n+1 frames, at most config/v.json "clip_max" (97, measured in the VRAM plan). A shot of n frames
is one clip of the smallest 8n+1 length >= n, or a chain of 97-frame clips; each later clip starts from the last frame
of the one before (one frame of overlap, dropped in the join). Each clip's depth video and first frame are kept next
to the take (<shot>_s<seed>_c<k>.*) so any clip can be re-run.
A shot in config/v.json "guide" follows its depth at that strength instead of 1 (a person who has to move more
than their rigid Blender stand-in).
A shot in config/v.json "reverse" is generated backwards: its plate's depth runs last frame first, clip 0 starts
from a keyframe of the plate's last frame, and the joined take is reversed (S09: the pan ends on the sign, which
forward runs could not keep). Every clip is a row in log/production_log.md.

Usage: .venv/bin/python scripts/v_batch.py plates [shot ...] [--jobs 4]
       .venv/bin/python scripts/v_batch.py gen [shot ...] [--seeds 1,2]   (ComfyUI must be running)
"""
import argparse
import datetime
import json
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import comfy_client as cc  # noqa: E402
from ltx_v import NEGATIVE, TEMPLATE, build  # noqa: E402

CFG = json.load(open("config/v.json"))
PICKS = json.load(open("config/keyframe_picks.json"))["picks"]
SHOTS_B = json.load(open("config/shots_b.json"))["shots"]
TIMES = json.load(open("timing/shot_times.json"))["shots"]
PLATES = Path("renders/b/v_plates")
OUT = Path("takes/v")
LOG = Path("log/production_log.md")
FPS = 24


def span(shot):
    """The shot's own frames [s0, s1), as render_shot.py computes them (montage parts split their cue evenly)."""
    b = SHOTS_B[shot]
    t = TIMES[b["time"]]
    s0, s1 = t["start_frame"], t["end_frame"]
    if "part" in b:
        k, n = b["part"]
        step = (s1 - s0) / n
        s0, s1 = round(t["start_frame"] + k * step), round(t["start_frame"] + (k + 1) * step)
    return s0, s1


def clip_plan(n):
    """Clip lengths (each 8k+1, at most clip_max) covering n frames, chained with one frame of overlap."""
    cmax = CFG["clip_max"]
    if n <= cmax:
        return [max(9, 8 * math.ceil((n - 1) / 8) + 1)]
    plan, covered = [cmax], cmax
    while covered < n:
        rest = n - covered + 1
        plan.append(cmax if rest > cmax else max(9, 8 * math.ceil((rest - 1) / 8) + 1))
        covered += plan[-1] - 1
    return plan


def plate_frames(shot):
    s0, s1 = span(shot)
    plan = clip_plan(s1 - s0)
    return s0, s0 + sum(plan) - (len(plan) - 1)


def size(shot):
    w, h = CFG["size"]
    return (h, w) if SHOTS_B[shot].get("vertical") else (w, h)


def plates(shots, jobs=1):
    """Render plates, several Blender processes at once: one process keeps the GPU at about 25% (most of each frame
    is CPU work: scene evaluation and writing the passes), and each needs only about 2 GB of VRAM and of RAM."""
    w, h = CFG["size"]

    def one(shot):
        a, b = plate_frames(shot)
        cmd = ["blender", "-b", "scenes/town.blend", "--python", "scripts/blender/render_shot.py", "--", shot,
               "--frames", f"{a}:{b}", "--res", f"{w}x{h}", "--samples", "32", "--out", str(PLATES)]
        t0 = datetime.datetime.now()
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{shot}: frames {a}-{b - 1} in {(datetime.datetime.now() - t0).seconds} s", flush=True)

    with ThreadPoolExecutor(jobs) as ex:
        list(ex.map(one, shots))


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def join(clips, n, final):
    """Join chained clips: drop each later clip's first frame (it repeats the clip before) and keep the shot's own n
    frames. Frames are re-timed by index (setpts=N), never resampled by time, so no frame is dropped or doubled even
    if a clip's frame rate differs (the template's default was 25 fps)."""
    parts = [f"[{i}:v]{'trim=start_frame=1,' if i else ''}setpts=PTS-STARTPTS,setsar=1[v{i}]" for i in range(len(clips))]
    ins = [x for c in clips for x in ("-i", str(c))]
    ffmpeg(*ins, "-filter_complex",
           ";".join(parts) + ";" + "".join(f"[v{i}]" for i in range(len(clips)))
           + f"concat=n={len(clips)}:v=1:a=0,trim=end_frame={n},setpts=N/{FPS}/TB,fps={FPS}[out]",
           "-map", "[out]", "-c:v", "libx264", "-crf", "14",
           "-pix_fmt", "yuv420p", str(final))


def gen(shots, seeds):
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    header = [False]

    def log_row(shot, seed, k, fr, depth, first, take, secs):
        """Append the clip's row right away, so a run that is stopped part way loses no log entries."""
        with open(LOG, "a") as f:
            if not header[0]:
                header[0] = True
                f.write(f"\n## {started} — V: shots ({', '.join(shots)})\n\n"
                        f"- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; "
                        f"template `{TEMPLATE}`; 8 steps, euler_ancestral, cfg 1; {CFG['size'][0]}×{CFG['size'][1]}. "
                        f"Control: the Blender depth pass. First frame: the approved keyframe (clip 0) or the previous "
                        f"clip's last frame.\n"
                        f"- **Prompts:** `config/v.json` (shot prompt + style); negative `NEGATIVE` in "
                        f"`scripts/ltx_v.py`. **Command:** `.venv/bin/python scripts/v_batch.py gen {' '.join(shots)} "
                        f"--seeds {','.join(map(str, seeds))}`\n\n"
                        f"| Shot | Seed | Clip | Plate frames | Control | First frame | Output | Seconds | Status |\n"
                        f"| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
            f.write(f"| {shot} | {seed} | {k} | {fr} | `{depth}` | `{first}` | `{take}` | {secs} | pending [H] |\n")

    for shot in shots:
        s0, s1 = span(shot)
        plan = clip_plan(s1 - s0)
        w, h = size(shot)
        prompt = f"{CFG['shots'][shot]} {CFG['style']}"
        pick = PICKS[shot] if isinstance(PICKS[shot], str) else PICKS[shot]["file"]
        key, src, n = f"takes/keyframes/{shot}/{pick}", PLATES / shot / "depth", s1 - s0
        rev = CFG.get("reverse", {}).get(shot)
        if rev:  # generate the plate backwards from a keyframe of its last frame, then play the take forwards
            a, b = plate_frames(shot)
            key, src, n = f"takes/keyframes/{rev}", PLATES / f"{shot}_reverse" / "depth", b - a
            src.mkdir(parents=True, exist_ok=True)
            for i, f in enumerate(range(b - 1, a - 1, -1)):
                link = src / f"{a + i:05d}.png"
                link.unlink(missing_ok=True)
                link.symlink_to((PLATES / shot / "depth" / f"{f:05d}.png").resolve())
        d = OUT / shot
        d.mkdir(parents=True, exist_ok=True)
        for seed in seeds:
            final = d / f"{shot}_s{seed}.mp4"
            if final.exists():
                continue
            first = d / f"{shot}_s{seed}_c0_first.png"
            ffmpeg("-i", key, "-vf", f"scale={w}:{h}:flags=lanczos", str(first))
            start, clips = s0, []
            for k, length in enumerate(plan):
                depth = d / f"{shot}_s{seed}_c{k}_depth.mp4"
                ffmpeg("-framerate", str(FPS), "-start_number", str(start), "-i", str(src / "%05d.png"),
                       "-frames:v", str(length), "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(depth))
                take = d / f"{shot}_s{seed}_c{k}.mp4"
                g = build(cc.upload_image(depth), cc.upload_image(first), prompt, seed, w, h,
                          f"folks/v_{shot}_s{seed}_c{k}", guide=CFG.get("guide", {}).get(shot, 1.0))
                outputs, secs = cc.run(g, timeout=7200)
                vid = next(v for kk, vs in outputs["68"].items() if kk in ("images", "videos", "gifs") for v in vs)
                cc.download(vid, take)
                log_row(shot, seed, k, f"{start}-{start + length - 1}", str(depth), str(first), str(take),
                        round(secs, 1))
                print(f"{shot} seed {seed} clip {k}: frames {start}-{start + length - 1}, {secs:.1f} s")
                clips.append(take)
                if k + 1 < len(plan):  # the next clip starts from this clip's last frame
                    first = d / f"{shot}_s{seed}_c{k + 1}_first.png"
                    ffmpeg("-sseof", "-0.1", "-i", str(take), "-update", "1", "-frames:v", "1", str(first))
                    start += length - 1
            if rev:
                backwards = d / f"{shot}_s{seed}_backwards.mp4"
                join(clips, n, backwards)
                ffmpeg("-i", str(backwards), "-vf", f"reverse,trim=end_frame={s1 - s0},setpts=N/{FPS}/TB",
                       "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(final))
            else:
                join(clips, n, final)
            print(f"{shot} seed {seed}: {final} ({s1 - s0} frames)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["plates", "gen"])
    ap.add_argument("shots", nargs="*")
    ap.add_argument("--seeds")
    ap.add_argument("--jobs", type=int, default=4, help="plates: Blender processes at once")
    a = ap.parse_args()
    shots = a.shots or list(CFG["shots"])
    if a.step == "plates":
        plates(shots, a.jobs)
    else:
        gen(shots, [int(s) for s in a.seeds.split(",")] if a.seeds else CFG["seeds"])


if __name__ == "__main__":
    main()
