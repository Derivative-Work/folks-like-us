"""E: cut, composite and mux Folks Like Us (config/edit.json).

Song frames follow the song's shot times, except where config/edit.json "cuts" moves a shot's boundaries; a shot's
picture stays in song sync (see the config note). Every output frame is built in numpy from the approved pictures:
  1. the shot's picture (an L, V or G take, a still with a push-in, or a card), scaled to the 1920x1056 stage
     (the takes x 1.5);
  2. O's surface layer (takes/o/surface/<shot>/), by multiply (ink takes the shot's light) or screen (S15, S16);
  3. S20/S23: the TV wall, each screen's content warped into its tracked quad (takes/o/tracks/), except where a
     diner stands in front (person masks from scripts/e_people.py);
  4. filled to 1920x1080 (scaled to 1080 high, centre-cropped), then the grade: halation round the highlights and
     fine grain, the same on every shot (style spec);
  5. O's screen layer (label, captions, lower thirds, counters, fine print).
Cards (title, fact, the closing vote note) are full-frame O renders and skip 1-4; S34 is the spectrogram with O's
line faded in over its top.

Each segment is encoded on its own (libx264 crf 14), in parallel, and the segments are joined in order; the audio is
the cold open's with-fallback span, the no-fallback master, and a low hum under the outro and the bookends.
The vertical cut (S29v-S31v, its label card and the vote note) is built the same way at 1080x1920.

Outputs: takes/e/folks_like_us_main.mp4, takes/e/folks_like_us_vertical.mp4 (git-ignored); segments in
takes/e/segments/. Usage: .venv/bin/python scripts/e_edit.py [main|vertical|all] [--jobs 6] [--only SEG ...]
"""
import argparse
import json
import subprocess
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont


CFG = json.load(open("config/edit.json"))
TIMES = json.load(open("timing/shot_times.json"))["shots"]
V = json.load(open("config/v_picks.json"))["picks"]
L = json.load(open("config/l_picks.json"))["picks"]
O_CFG = json.load(open("config/o.json"))
FPS = 24
OUT = Path("takes/e")
STAGE = (1920, 1056)
MASTER = "audio/master/folks_like_us_master_nofallback.wav"
FALLBACK = "audio/master/with-fallback/folks_like_us_master_withfallback.wav"
FONT = "assets/fonts/SourceSans3[wght].ttf"


CUTS = CFG["cuts"]
PARTS = ("S27a", "S27b", "S27c", "S27d", "S27e", "S28a", "S28b")


def shot_at(f, cold=False):
    """The shot on screen at song frame f: config "cuts" first, then the song's shot times. The cold open is the
    hook from S29 on, so it takes the song's shot times only (the montage's cuts reach into S29's frames)."""
    for s, (a, b) in ({} if cold else CUTS).items():
        if a <= f < b:
            return s
    return next(s for s, t in TIMES.items() if t["start_frame"] <= f < t["end_frame"])


def cut_starts():
    """Every frame where the picture cuts (the main cut's song segments are split there)."""
    starts = {t["start_frame"] for s, t in TIMES.items() if s not in CUTS and s not in ("S27", "S28")}
    return sorted(starts | {a for a, b in CUTS.values()})


def vpick(shot):
    p = V[shot]
    return f"takes/v/{shot}/{p if isinstance(p, str) else p['file']}"


def ffmpeg(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


@lru_cache(maxsize=12)
def video(path):
    """All frames of a video, as uint8 [n, h, w, 3]."""
    w, h = (int(x) for x in subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0",
         path], capture_output=True, text=True, check=True).stdout.strip().split(","))
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


@lru_cache(maxsize=8)
def still(path):
    return Image.open(path).convert("RGB")


def frame_of(path, i):
    if path.endswith(".png"):
        return still(path)
    v = video(path)
    return Image.fromarray(v[min(max(i, 0), len(v) - 1)])


def overlay(path):
    p = Path(path)
    return Image.open(p).convert("RGBA") if p.exists() else None


def multiply(base, ov):
    b = np.asarray(base, np.float32) / 255
    a = np.asarray(ov, np.float32) / 255
    al = a[..., 3:]
    return Image.fromarray(((b * (1 - al + al * a[..., :3])) * 255 + 0.5).astype(np.uint8))


def screen_blend(base, ov):
    b = np.asarray(base, np.float32) / 255
    a = np.asarray(ov, np.float32) / 255
    s = 1 - (1 - b) * (1 - a[..., :3])
    al = a[..., 3:]
    return Image.fromarray(((b * (1 - al) + s * al) * 255 + 0.5).astype(np.uint8))


def over(base, ov):
    base = base.convert("RGBA")
    base.alpha_composite(ov)
    return base.convert("RGB")


def perspective_coeffs(dst, src):
    """PIL PERSPECTIVE coefficients mapping output points dst to input points src."""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        b += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(b, float)).tolist()


def fill(img, size):
    """Scale to fill size (cover) and centre-crop."""
    w, h = size
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def push(img, size, z, centre=None):
    """A push-in: crop 1/z of the image round centre, filled to size."""
    cx, cy = centre or (img.width / 2, img.height / 2)
    w, h = img.width / z, img.height / z
    left, top = min(max(cx - w / 2, 0), img.width - w), min(max(cy - h / 2, 0), img.height - h)
    return fill(img.crop((round(left), round(top), round(left + w), round(top + h))), size)


def grade(img, n):
    g = CFG["grade"]
    a = np.asarray(img, np.float32) / 255
    lum = a @ np.array([0.299, 0.587, 0.114], np.float32)
    hi = np.clip((lum - g["halation_threshold"]) / (1 - g["halation_threshold"]), 0, 1)[..., None] ** 2 * a
    small = Image.fromarray((hi * 255).astype(np.uint8)).resize((img.width // 4, img.height // 4), Image.BILINEAR)
    glow = np.asarray(small.filter(ImageFilter.GaussianBlur(6)).resize(img.size, Image.BILINEAR), np.float32) / 255
    a = a + g["halation"] * glow * np.array([1.0, 0.55, 0.35], np.float32)
    rng = np.random.default_rng(n)
    a = a + rng.normal(0, g["grain"], a.shape[:2]).astype(np.float32)[..., None]
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))


# ---------------------------------------------------------------- the TV wall (S20, S23)

TVS = "ABCDEFGHI"


@lru_cache(maxsize=1)
def tv_quads():
    return {k: np.asarray(json.load(open(f"takes/o/tracks/S20__tv_{k}.json"))["quads"]) * 1.5 for k in TVS}


@lru_cache(maxsize=2)
def tractor():
    im = still(CFG["tv"]["S20"]["B"][0]).copy()  # blur the hood's garbled lettering (legible text is O's)
    box = CFG["tv"]["tractor_blur_box"]
    im.paste(im.crop(box).filter(ImageFilter.GaussianBlur(10)), box[:2])
    return im


@lru_cache(maxsize=4)
def people(i):
    """The diners in front of the TV wall on S20 take frame i (scripts/e_people.py), stage size, grown and feathered."""
    t = CFG["tv"]
    m = Image.open(f"{t['people']}/{i:05d}.png").resize(STAGE, Image.BILINEAR)
    return m.filter(ImageFilter.MaxFilter(t["person_grow"])).filter(ImageFilter.GaussianBlur(1.2))


def tv_wall(base, i, sources, j):
    """Composite the TV content onto the stage-size base frame i (S20 take frame); j is the content frame. Each
    screen's tracked quad is filled, except where a diner stands in front of it."""
    t = CFG["tv"]
    front = np.asarray(people(min(i, len(tv_quads()["A"]) - 1)), np.float32) / 255
    out = base.copy()
    for k in TVS:
        q = tv_quads()[k][min(i, len(tv_quads()[k]) - 1)]
        c = q.mean(0)
        q = c + (q - c) * (1 - t["inset"])
        path, off = sources[k] if isinstance(sources, dict) else (sources, 0)
        if path == t["S20"]["B"][0]:
            src = tractor()
        else:  # TV content loops
            src = frame_of(path, (j + off) % (1 if path.endswith(".png") else len(video(path))))
        if path.endswith(".png"):  # a still on a TV: a slow push-in
            src = push(src, src.size, 1 + 0.002 * j)
        w, h = src.size
        warped = src.transform(STAGE, Image.PERSPECTIVE, perspective_coeffs(q.tolist(), [(0, 0), (w, 0), (w, h), (0, h)]),
                               Image.BILINEAR)
        m = Image.new("L", STAGE, 0)
        ImageDraw.Draw(m).polygon([tuple(p) for p in q], fill=255)
        m = Image.fromarray((np.asarray(m, np.float32) * (1 - front)).astype(np.uint8))
        lit = Image.fromarray((np.asarray(warped, np.float32) * 0.88 + 8).clip(0, 255).astype(np.uint8))
        out.paste(lit, (0, 0), m)
    return out


# ---------------------------------------------------------------- shots

def stage_of(path, i):
    return frame_of(path, i).resize(STAGE, Image.LANCZOS)


def with_surface(img, shot_dir, i, blend):
    ov = overlay(f"takes/o/surface/{shot_dir}/{i:05d}.png")
    if ov is None:
        return img
    return screen_blend(img, ov) if blend == "screen" else multiply(img, ov)


def card(name, i):
    return Image.open(f"takes/o/cards/{name}/{i:05d}.png").convert("RGB")


def placeholder(text, size):
    im = Image.new("RGB", size, (16, 16, 20))
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(FONT, 44)
    font.set_variation_by_axes([600])
    d.multiline_text((size[0] // 2, size[1] // 2), text.replace(" ([H]", "\n([H]"), font=font, fill=(235, 235, 235),
                     anchor="mm", align="center")
    return im


def song_picture(f, cold=False):
    """Stage-size (or full-frame card) picture for song frame f, and whether it is a card."""
    sh = shot_at(f, cold)
    loc = f - TIMES[sh]["start_frame"] if sh in TIMES else 0
    blend = O_CFG["blend"].get(sh, O_CFG["blend"]["default"])
    if sh == "S04":
        i0, i1 = CFG["intro"]["S02"]
        if f < i1:
            return card("title", f - i0), True
        i0, i1 = CFG["intro"]["S03"]
        if f < i1:
            return placeholder(CFG["placeholders"]["S03"], CFG["size"]), True
        return stage_of(vpick("S04"), f), False
    if sh == "S07":
        n = TIMES[sh]["end_frame"] - TIMES[sh]["start_frame"]
        z0, z1 = CFG["s07"]["zoom"]
        return push(still(CFG["s07"]["still"]), STAGE, z0 + (z1 - z0) * loc / (n - 1)), False
    if sh == "S10":
        return stage_of(f"takes/l/S10/{CFG['extra_picks']['S10']}", min(loc, CFG["s10_hold_from"])), False
    if sh == "S19c":  # the close crop: S19's plate frames 77 down to 4 (config/l.json), the face and the pointing hand
        c = CFG["s19c"]
        i = f - CUTS[sh][0]
        img = frame_of(f"takes/l/S19c/{c['pick']}", i).crop(c["crop"]).resize(STAGE, Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(*c["sharpen"]))
        return img, False
    if sh == "S21":  # S19's frames from 0: the chair keeps its TBD tag
        return with_surface(stage_of(f"takes/l/S21/{CFG['extra_picks'][sh]}", loc), "S19", loc, "multiply"), False
    if sh == "S30":  # the building's LED blinks
        img = stage_of(f"takes/l/{sh}/{CFG['extra_picks'][sh]}", loc)
        led = CFG["s30_led"]
        if int(loc / FPS * led["hz"] * 2) % 2 == 0:
            x, y = (c * 1.5 for c in led["at"])
            for r, a in ((led["radius"] * 4, 40), (led["radius"] * 2, 110), (led["radius"], 255)):
                glow = Image.new("RGBA", STAGE, (0, 0, 0, 0))
                ImageDraw.Draw(glow).ellipse([x - r, y - r, x + r, y + r], fill=(255, 40, 30, a))
                img = over(img, glow.filter(ImageFilter.GaussianBlur(r / 2)))
        return img, False
    if sh == "S17":
        a, b = CFG["s17_insert"]["song_frames"]
        if a <= f < b:
            z0, z1 = CFG["s17_insert"]["zoom"]
            base = with_surface(still("takes/g/assets/recipe_card/recipe_card_s3102.png"), "S17i", 0, "multiply")
            return push(base, STAGE, z0 + (z1 - z0) * (f - a) / (b - a - 1)), False
        return stage_of(vpick("S17"), loc), False
    if sh == "S20":
        return tv_wall(stage_of(vpick("S20"), loc), loc, CFG["tv"]["S20"], loc), False
    if sh == "S23":
        return tv_wall(stage_of(vpick("S20"), loc), loc, CFG["tv"]["S23"], loc), False
    if sh == "S24":
        return with_surface(stage_of(f"takes/l/S05/{L['S05']}", loc), "S24", loc, blend), False
    if sh == "S26":  # re-synced 14 frames earlier into S25's slot (S25 is cut)
        i = f - CUTS[sh][0]
        return with_surface(stage_of(f"takes/l/S26x/{CFG['extra_picks']['S26x']}", i), sh, i, blend), False
    if sh in PARTS:
        pl = f - CUTS[sh][0]
        return with_surface(stage_of(vpick(sh), pl), sh, pl, O_CFG["blend"].get(sh, O_CFG["blend"]["default"])), False
    if sh in ("S29", "S32", "S33"):
        if sh == "S29" and cold:  # the cold open has no G pass
            return stage_of(f"takes/l/S29/{L['S29']}", loc), False
        return stage_of(f"takes/g/{sh}/{sh}_g.mp4", loc), False
    src = f"takes/l/{sh}/{L[sh]}" if sh in L else vpick(sh)
    return with_surface(stage_of(src, loc), sh, loc, blend), False


def finish(pic, is_card, n, screen, size=None):
    if not is_card:
        pic = grade(fill(pic, size or CFG["size"]), n)
    if screen is not None:
        pic = over(pic, screen)
    return pic


# ---------------------------------------------------------------- segments

def segments_main():
    """(name, kind, frames): the main cut in order. Song segments are split at shot boundaries."""
    segs = [("00_cold_open", "cold", list(range(*CFG["cold_open"]["song_frames"])))]
    starts = sorted({0, *CFG["intro"]["S03"], *cut_starts(), 3389})
    for k, (a, b) in enumerate(zip(starts, starts[1:])):
        segs.append((f"{k + 1:02d}_song_{a:05d}", "song", list(range(a, b))))
    n = len(segs)
    for k, (name, frames) in enumerate(CFG["bookends"].items()):
        segs.append((f"{n + k:02d}_{name}", name, list(range(frames))))
    return segs


def s34(k, n):
    """The spectrogram, scaled down under O's line (which fades in over the top), with a slow push-in."""
    c = CFG["s34"]
    w, h = CFG["size"]
    plot = still("takes/g/S34/S34_spectrogram.png")
    pw, ph = round(w * c["plot_scale"]), round(h * c["plot_scale"])
    plot = push(plot, (pw, ph), 1 + c["push"] * k / (n - 1))
    img = Image.new("RGB", (w, h), plot.getpixel((4, 4)))
    img.paste(plot, ((w - pw) // 2, c["plot_top"]))
    a, b = c["text_fade"]
    text = overlay("takes/o/cards/s34_over/00011.png")  # past the card's own 0.3 s fade-in
    alpha = min(max((k - a) / (b - a), 0), 1)
    if alpha > 0:
        text.putalpha(Image.fromarray((np.asarray(text.getchannel("A"), np.float32) * alpha).astype(np.uint8)))
        img = over(img, text)
    return img


def s35(k):
    """The FEC pages, each panned down its full-page screenshot, then the planning chat (which carries its own label)."""
    c = CFG["s35"]
    for p in c["fec"]:
        if k < p["frames"]:
            u = k / (p["frames"] - 1)
            y0, y1 = p["y"]
            y = round(y0 + (y1 - y0) * (u * u * (3 - 2 * u)))  # eased, like a hand on the scroll wheel
            x, w = p["x"], p["w"]
            page = still(f"takes/s35/fec/{p['page']}.png")
            return over(page.crop((x, y, x + w, y + w * 9 // 16)).resize(CFG["size"], Image.LANCZOS), label_layer())
        k -= p["frames"]
    return Image.open(f"takes/s35/chat/{k:05d}.png").convert("RGB")


@lru_cache(maxsize=1)
def label_layer():
    return overlay("takes/o/screen/00000.png")  # song frame 0: the label alone


def render_main(seg):
    name, kind, frames = seg
    video.cache_clear()  # a worker renders several segments; keep only this one's videos
    out = OUT / "segments" / f"{name}.mp4"
    w, h = CFG["size"]
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "14", "-preset", "medium",
                          "-pix_fmt", "yuv420p", str(out)], stdin=subprocess.PIPE)
    for k, f in enumerate(frames):
        if kind in ("song", "cold"):
            pic, is_card = song_picture(f, cold=(kind == "cold"))
            scr = overlay(f"takes/o/{'screen_nojitter' if kind == 'cold' else 'screen'}/{f:05d}.png")
            if is_card and f < CFG["intro"]["S02"][1]:
                scr = None  # the title card carries its own label
            img = finish(pic, is_card, f + (100000 if kind == "cold" else 0), scr)
        elif kind == "S33_tail":  # S33's G pass runs a second past the song: the building alone, over the hum
            img = finish(stage_of("takes/g/S33/S33_g.mp4", TIMES["S33"]["end_frame"] - TIMES["S33"]["start_frame"] + k),
                         False, 300000 + k, label_layer())
        elif kind == "S34":
            img = over(s34(k, len(frames)), label_layer())
        elif kind == "S35":
            img = s35(k)
        elif kind == "S36":
            img = card("fact", k)
        else:
            img = card("vote", min(k, 23))  # the card holds after its fade-in
        assert img.size == (w, h), (name, f, img.size)
        p.stdin.write(np.asarray(img.convert("RGB")).tobytes())
    p.stdin.close()
    p.wait()
    return str(out), len(frames)


def render_vertical(seg):
    name, kind, frames = seg
    out = OUT / "segments_vertical" / f"{name}.mp4"
    w, h = CFG["vertical"]["size"]
    vstage = (STAGE[1], STAGE[0])
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(out)],
                         stdin=subprocess.PIPE)
    for k, f in enumerate(frames):
        if kind == "label":
            img = card("labelcard", k)
        elif kind == "vote":
            img = card("vote_portrait", min(k, 23))
        else:
            sh = next(s for s in ("S29", "S30", "S31") if TIMES[s]["start_frame"] <= f < TIMES[s]["end_frame"])
            loc = f - TIMES[sh]["start_frame"]
            if sh == "S29":
                pic = frame_of("takes/g/S29v/S29v_g.mp4", loc).resize(vstage, Image.LANCZOS)
            elif sh == "S30":
                pic = frame_of(f"takes/l/S30v/{CFG['extra_picks']['S30v']}", loc).resize(vstage, Image.LANCZOS)
            else:
                pic = with_surface(frame_of(vpick("S31v"), loc).resize(vstage, Image.LANCZOS), "S31v", loc, "multiply")
            img = finish(pic, False, 200000 + f, overlay(f"takes/o/screen_portrait/{f:05d}.png"), (w, h))
        assert img.size == (w, h), (name, f, img.size)  # a wrong size has the right byte count and scrambles silently
        p.stdin.write(np.asarray(img.convert("RGB")).tobytes())
    p.stdin.close()
    p.wait()
    return str(out), len(frames)


# ---------------------------------------------------------------- audio and assembly

def hum(seconds, sr=48000):
    """A low data-centre hum: mains harmonics and filtered fan noise, slowly breathing."""
    t = np.arange(int(seconds * sr)) / sr
    rng = np.random.default_rng(7)
    noise = np.convolve(rng.normal(0, 1, t.size), np.ones(400) / 400, mode="same")
    y = (0.5 * np.sin(2 * np.pi * 60 * t) + 0.3 * np.sin(2 * np.pi * 120 * t) + 0.15 * np.sin(2 * np.pi * 180 * t)
         + 2.5 * noise) * (1 + 0.15 * np.sin(2 * np.pi * 0.2 * t))
    y = y / np.abs(y).max() * 10 ** (CFG["hum"]["level_db"] / 20)
    return np.stack([y, y], 1).astype(np.float32)


def audio_main(cold_n, song_n, tail_n, path):
    import soundfile as sf
    sr = 48000
    cold_a, cold_b = (f / FPS for f in CFG["cold_open"]["song_frames"])
    fb, _ = sf.read(FALLBACK, dtype="float32", always_2d=True)
    ma, msr = sf.read(MASTER, dtype="float32", always_2d=True)
    assert msr == sr, msr
    cold = fb[int(cold_a * sr):int(cold_a * sr) + round(cold_n / FPS * sr)].copy()
    fo = int(CFG["cold_open"]["fade_out_s"] * sr)
    cold[-fo:] *= np.linspace(1, 0, fo)[:, None]
    song = ma[:round(song_n / FPS * sr)]
    song = np.pad(song, ((0, round(song_n / FPS * sr) - len(song)), (0, 0)))
    tail = np.zeros((round(tail_n / FPS * sr), 2), np.float32)
    mix = np.concatenate([cold, song, tail])
    h0 = len(cold) + int(CFG["hum"]["start_song_s"] * sr)
    hm = hum((len(mix) - h0) / sr)
    ramp = np.minimum(1, np.arange(len(hm)) / (4 * sr))[:, None]
    fade = np.minimum(1, (len(hm) - np.arange(len(hm))) / (CFG["hum"]["fade_out_s"] * sr))[:, None]
    mix[h0:] += hm * ramp * fade
    sf.write(path, mix, sr, subtype="PCM_24")


def assemble(seg_paths, audio, out):
    lst = out.with_suffix(".txt")
    lst.write_text("".join(f"file '{Path(p).resolve()}'\n" for p in seg_paths))
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(audio), "-map", "0:v", "-map", "1:a",
           "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", str(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", nargs="?", default="all", choices=["main", "vertical", "all"])
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--only", nargs="*", help="re-render these segments only (names), then reassemble")
    a = ap.parse_args()
    (OUT / "segments").mkdir(parents=True, exist_ok=True)
    (OUT / "segments_vertical").mkdir(parents=True, exist_ok=True)
    if a.what in ("main", "all"):
        segs = segments_main()
        todo = [s for s in segs if not a.only or s[0] in a.only]
        with ProcessPoolExecutor(a.jobs) as ex:
            for path, n in ex.map(render_main, sorted(todo, key=lambda s: -len(s[2]))):
                print(f"{path}: {n} frames", flush=True)
        cold_n = len(segs[0][2])
        song_n = sum(len(s[2]) for s in segs if s[1] == "song")
        tail_n = sum(len(s[2]) for s in segs if s[1] not in ("song", "cold"))
        audio = OUT / "main_audio.wav"
        audio_main(cold_n, song_n, tail_n, audio)
        assemble([OUT / "segments" / f"{s[0]}.mp4" for s in segs], audio, OUT / "folks_like_us_main.mp4")
        print(f"main: {cold_n + song_n + tail_n} frames, {(cold_n + song_n + tail_n) / FPS:.1f} s")
    if a.what in ("vertical", "all"):
        a0, a1 = CFG["vertical"]["song_frames"]
        segs = [("v0_song", "song", list(range(a0, a1))), ("v1_label", "label", list(range(CFG["vertical"]["label_card"]))),
                ("v2_vote", "vote", list(range(CFG["vertical"]["vote_card"])))]
        with ProcessPoolExecutor(3) as ex:
            for path, n in ex.map(render_vertical, segs):
                print(f"{path}: {n} frames", flush=True)
        import soundfile as sf
        ma, sr = sf.read(MASTER, dtype="float32", always_2d=True)
        song = ma[int(a0 / FPS * sr):int(a0 / FPS * sr) + round((a1 - a0) / FPS * sr)]
        lab = ma[len(song) + int(a0 / FPS * sr):][:round(CFG["vertical"]["label_card"] / FPS * sr)].copy()
        lab *= np.linspace(1, 0, len(lab))[:, None]
        quiet = np.zeros((round(CFG["vertical"]["vote_card"] / FPS * sr), song.shape[1]), np.float32)
        sf.write(OUT / "vertical_audio.wav", np.concatenate([song, lab, quiet]), sr, subtype="PCM_24")
        assemble([OUT / "segments_vertical" / f"{s[0]}.mp4" for s in segs], OUT / "vertical_audio.wav",
                 OUT / "folks_like_us_vertical.mp4")
        print("vertical:", (a1 - a0 + CFG["vertical"]["label_card"] + CFG["vertical"]["vote_card"]) / FPS, "s")


if __name__ == "__main__":
    main()
