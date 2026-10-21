"""G: the glitch and decay passes, each cut to its F region's exact frames (timing/failure_map.json). A frame is
inside a region when its time, frame / 24, falls in [start, end); every other frame is the input untouched.

  S29, S29v  (F1)  the L take; the raised hand flashes six fingers (g_assets.py edits, pasted for `flash` frames) and
                   one frame of sky is a wall of server racks (the sky from the plate's depth pass, feathered).
                   The flag's wrong-way ripple is cut: the flag is outside both frames (log/decisions.md).
  S32        (F2)  the frozen smile: S33's keyframe held for the whole disclaimer with a slow push-in; inside F2 the
                   smile flickers to the wrong-smile edit and back. F3 starts 10 frames before S32 ends; those
                   frames are re-encoded lossier each frame, ending near the decay's first generation.
  S33        (F3)  the decay generations (g_decay.py), ramped from gen1 to the last over F3; the building is
                   composited back sharp from gen0 through a mask measured on the take; over the last second everything but the
                   building fades to black, so the shot ends on the building alone.
Outputs: takes/g/<shot>/<shot>_g.mp4 (picture only) and _audio.mp4 (with the master). One log row per shot.

Usage: .venv/bin/python scripts/g_pass.py [shot ...]
"""
import datetime
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).parent))
from v_batch import FPS, span  # noqa: E402

CFG = json.load(open("config/g.json"))
FMAP = json.load(open("timing/failure_map.json"))["regions"]
TIMES = json.load(open("timing/shot_times.json"))["shots"]
L_PICKS = json.load(open("config/l_picks.json"))["picks"]
PLATES = Path("renders/b/v_plates")
OUT = Path("takes/g")
LOG = Path("log/production_log.md")
MASTER = "audio/master/folks_like_us_master_nofallback.wav"
SIZE = (1280, 704)


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def frames_of(video, dest):
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True)
    ffmpeg("-i", str(video), str(dest / "%05d.png"))
    return sorted(dest.glob("*.png"))


def inside(region, frame):
    """Whether absolute frame `frame` is inside F region `region`."""
    r = FMAP[region]
    return r["start"] <= frame / FPS < r["end"]


def circle(size, feather):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).ellipse([feather, feather, size[0] - feather, size[1] - feather], fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather / 2))


def asset(name):
    """The picked edit of an asset (config "picks": its frame and seed)."""
    p = CFG["picks"][name]
    return Image.open(Path("takes/g/assets") / name / f"f{p['frame']}_s{p['seed']}.png").convert("RGB")


def sky(shot, abs_frame):
    a = np.asarray(Image.open(PLATES / shot / "depth" / f"{abs_frame:05d}.png")).astype(np.int32)
    m = Image.fromarray(((a <= a.min() + 50) * 255).astype(np.uint8))
    return m.filter(ImageFilter.GaussianBlur(2))


def racks(size):
    im = Image.open(Path("takes/g/assets/server_racks") / f"server_racks_s{CFG['picks']['server_racks']}.png")
    im = im.crop((0, round(im.height * CFG["racks_top"]), im.width, im.height))  # below the ceiling lights
    w, h = size  # cover-crop to the frame
    s = max(w / im.width, h / im.height)
    im = im.convert("RGB").resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def lossy(im, quality, scale):
    """A copy of a copy: scaled down, JPEG-compressed, scaled back up."""
    w, h = im.size
    small = im.resize((max(16, int(w * scale)), max(16, int(h * scale))), Image.BILINEAR)
    buf = io.BytesIO()
    small.save(buf, "JPEG", quality=quality)
    return Image.open(buf).convert("RGB").resize((w, h), Image.BILINEAR)


def f1(shot):
    """S29 / S29v: six-finger flashes and one frame of server racks, inside F1 only."""
    s0, s1 = span(shot)
    work = OUT / shot / "frames"
    frames = frames_of(Path("takes/l") / shot / L_PICKS[shot], work)
    spec = CFG["f1"][shot]
    a = CFG["assets"][spec["fingers"]]
    x0, y0, x1, y1 = a["box"]
    mask = circle((x1 - x0, y1 - y0), 18)
    touched = []
    hand = asset(spec["fingers"])
    for f in spec["at"]:
        for i in range(f, f + spec["flash"]):
            if inside("F1", s0 + i):
                im = Image.open(frames[i]).convert("RGB")
                im.paste(hand, (x0, y0), mask)
                im.save(frames[i])
                touched.append(i)
    i = spec["racks_frame"]
    if inside("F1", s0 + i):
        im = Image.open(frames[i]).convert("RGB")
        im.paste(racks(im.size), (0, 0), sky(shot, s0 + i))
        im.save(frames[i])
        touched.append(i)
    return frames, s0, s1, f"six fingers on frames {sorted(set(touched) - {i})}, server racks on frame {i}"


def s32():
    """The frozen smile under the disclaimer, the F2 smile flicker, and the start of F3."""
    s0, s1 = TIMES["S32"]["start_frame"], TIMES["S32"]["end_frame"]  # no B shot: E and G make it
    spec = CFG["s32"]
    work = OUT / "S32" / "frames"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    key = Image.open(spec["still"]).convert("RGB")
    a = CFG["assets"]["wrong_smile_S32"]
    x0, y0, x1, y1 = a["box"]
    wrong = key.copy()
    wrong.paste(asset("wrong_smile_S32"), (x0, y0), circle((x1 - x0, y1 - y0), 22))
    n = s1 - s0
    cx, cy = spec["push_centre"]
    f2 = [i for i in range(n) if inside("F2", s0 + i)]
    flick = {f2[0] + round(p * (len(f2) - 1)) + k for p in spec["flicker_at"] for k in range(spec["flicker_len"])}
    f3 = [i for i in range(n) if inside("F3", s0 + i)]
    for i in range(n):
        z = 1 + (spec["push_to"] - 1) * (i / (n - 1)) ** 1.5  # slow push-in, easing in
        src = wrong if i in flick else key
        w, h = src.width / z, src.height / z
        left = min(max(cx - w / 2, 0), src.width - w)
        top = min(max(cy - h / 2, 0), src.height - h)
        im = src.crop((round(left), round(top), round(left + w), round(top + h))).resize(SIZE, Image.LANCZOS)
        if i in f3:  # F3 begins: each frame a worse copy than the last
            k = f3.index(i) + 1
            im = lossy(im, max(22, 60 - 4 * k), max(0.5, 0.9 - 0.04 * k))  # ends near gen1's level
        im.save(work / f"{i + 1:05d}.png")
    return sorted(work.glob("*.png")), s0, s1, (f"S33 keyframe held, push-in to {spec['push_to']}x; wrong smile on "
                                                f"frames {sorted(flick)}; lossy decay on frames {f3[0]}-{f3[-1]}")


def building(spec):
    """S33's building mask: a polygon measured on the take (config "s33" "building"), minus the porch post in front
    of it, feathered. The camera is static. The plate's mask pass doesn't fit this take: LTX drew the building
    shorter than the layout's, and the layout's sloping porch roof hides part of it."""
    m = Image.new("L", SIZE, 0)
    d = ImageDraw.Draw(m)
    d.polygon([tuple(p) for p in spec["building"]], fill=255)
    for box in spec["in_front"]:
        d.rectangle(box, fill=0)
    return np.asarray(m.filter(ImageFilter.GaussianBlur(spec["mask_feather"])), np.float32)[..., None] / 255


def s33():
    """The decay generations ramped over F3, the building sharp through its mask, the end on the building alone."""
    s0, s1 = span("S33")
    spec = CFG["s33"]
    n = s1 - s0
    gens = CFG["decay"]["generations"]
    work = OUT / "S33" / "frames"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    g = lambda k, i: np.asarray(Image.open(OUT / "S33" / f"gen{k}" / f"{i + 1:05d}.png").convert("RGB"),  # noqa: E731
                                np.float32)
    f3 = [i for i in range(n) if inside("F3", s0 + i)]
    fade, alone = spec["fade_frames"], spec["alone_frames"]
    mask = building(spec)
    for i in range(n):
        if i in f3:
            pos = 1 + (gens - 1) * f3.index(i) / max(1, len(f3) - 1)  # gen1 at F3's start, the last gen at its end
            lo, hi = int(pos), min(gens, int(pos) + 1)
            t = pos - lo
            im = (1 - t) * g(lo, i) + t * g(hi, i)
        else:
            im = g(0, i)
        m = mask
        rest = max(0.0, min(1.0, (n - alone - i) / fade))  # fades out over `fade` frames, then `alone` on the building
        im = m * g(0, i) + (1 - m) * im * rest
        Image.fromarray(im.round().clip(0, 255).astype(np.uint8)).save(work / f"{i + 1:05d}.png")
    return sorted(work.glob("*.png")), s0, s1, (f"gen1-gen{gens} over F3 (frames {f3[0]}-{f3[-1]}), building from "
                                                f"gen0 through its measured mask, the rest fades out over {fade} and the building holds alone for {alone}")


def main():
    shots = sys.argv[1:] or ["S29", "S29v", "S32", "S33"]
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    rows = []
    for shot in shots:
        frames, s0, s1, what = f1(shot) if shot in ("S29", "S29v") else s32() if shot == "S32" else s33()
        d = OUT / shot
        out = d / f"{shot}_g.mp4"
        ffmpeg("-framerate", str(FPS), "-i", str(frames[0].parent / "%05d.png"), "-frames:v", str(s1 - s0),
               "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(out))
        ffmpeg("-i", str(out), "-ss", f"{s0 / FPS:.4f}", "-t", f"{(s1 - s0) / FPS:.4f}", "-i", MASTER, "-map", "0:v",
               "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(d / f"{shot}_g_audio.mp4"))
        rows.append((shot, f"{s0}-{s1 - 1}", what, str(out)))
        print(f"{shot}: {out} ({what})", flush=True)
    with open(LOG, "a") as fh:
        fh.write(f"\n## {started} — G: glitch and decay passes ({', '.join(shots)})\n\n"
                 f"- **Tool:** `scripts/g_pass.py` (Python, PIL, ffmpeg), cut to `timing/failure_map.json` (a frame is "
                 f"inside a region when frame / 24 falls in [start, end)). Settings and asset picks: `config/g.json`. "
                 f"**Command:** `.venv/bin/python scripts/g_pass.py {' '.join(sys.argv[1:])}`\n\n"
                 f"| Shot | Frames | What | Output | Status |\n| --- | --- | --- | --- | --- |\n")
        for r in rows:
            fh.write(f"| {r[0]} | {r[1]} | {r[2]} | `{r[3]}` | pending [H] |\n")


if __name__ == "__main__":
    main()
