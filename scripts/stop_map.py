"""Pre-production step 3: measure each stop in the mix and write timing/stops.json, with the edits E must make.

Measured: the master's level in each stop's vocal gap (from the timing map). Suno paused only the vocal: the band
plays through every gap, so the take has no silence to use and E makes all four (log/decisions.md).
Edits, in source (Suno take) time:
  - mute: the whole mix from the setup word's end to PREROLL before the swerve word (FADE ramps at both ends);
  - insert: silence of N beats at the setup word's end, where the gap is too short (ST3) or the stop is held
    longer (ST4). A whole number of beats keeps the groove on the beat grid after the stop.
stops.json also maps source time to edit time (each insert pushes everything after it later), and the script
renders a preview of the stopped master (audio/master/preview_stops.wav, git-ignored) for [H] to judge.

Usage: .venv/bin/python scripts/stop_map.py  ->  timing/stops.json, audio/master/preview_stops.wav
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf

MASTER = Path("audio/master/folks_like_us_master_nofallback.wav")
TIMING = Path("timing/timing_map.json")
OUT = Path("timing/stops.json")
PREVIEW = Path("audio/master/preview_stops.wav")
SILENT_DB = -60.0  # mix level that counts as silence (50 ms RMS frames)
PREROLL = 0.03     # resume the music this long before the swerve word, so its attack isn't cut
FADE = 0.01
# Beats of silence to insert at each stop's setup word (brief: one beat each; ST4 "held twice as long").
INSERT_BEATS = {"ST1": 0, "ST2": 0, "ST3": 1, "ST4": 1}


def frames_db(x, sr, frame_s=0.05):
    h = int(sr * frame_s)
    n = len(x) // h
    m = x[: n * h].reshape(n, h, -1) if x.ndim > 1 else x[: n * h].reshape(n, h)
    return 20 * np.log10(np.sqrt((m ** 2).mean(axis=tuple(range(1, m.ndim)))) + 1e-12)


def longest_run(mask):
    best = run = 0
    for v in mask:
        run = run + 1 if v else 0
        best = max(best, run)
    return best


def beat_period(beats, t):
    b = np.array(beats)
    i = np.searchsorted(b, t)
    near = np.diff(b[max(0, i - 4):i + 4])
    return float(np.median(near))


def main():
    x, sr = sf.read(MASTER, dtype="float64")
    tm = json.load(open(TIMING))
    db = frames_db(x, sr)
    stops, ops = {}, []
    for sid, c in tm["stops"].items():
        a, b = c["before"]["end"], c["after"]["start"]
        seg = db[int(a / 0.05):max(int(b / 0.05), int(a / 0.05) + 1)]
        silent_s = longest_run(seg < SILENT_DB) * 0.05
        period = beat_period(tm["beats"], a)
        mute = [a, max(a, b - PREROLL)]
        insert = round(INSERT_BEATS[sid] * period, 3)
        stops[sid] = {
            "section": c["section"], "setup_word": c["before"], "swerve_word": c["after"],
            "vocal_gap_s": c["gap_s"],
            "mix_db_in_gap": {"min": round(float(seg.min()), 1), "max": round(float(seg.max()), 1)},
            "real_silence_s": round(silent_s, 2),
            "made_by_edit": silent_s < 0.2,
            "beat_s": round(period, 3),
            "edit": {"mute": [round(mute[0], 3), round(mute[1], 3)], "insert_at": round(a, 3), "insert_s": insert},
            "silence_s": round(mute[1] - mute[0] + insert, 3),
        }
        if mute[1] > mute[0]:
            ops.append({"op": "mute", "stop": sid, "start": round(mute[0], 3), "end": round(mute[1], 3)})
        if insert:
            ops.append({"op": "insert_silence", "stop": sid, "at": round(a, 3), "duration": insert})
    # Source -> edit time: piecewise shifts after each insert.
    shifts, total = [], 0.0
    for o in sorted((o for o in ops if o["op"] == "insert_silence"), key=lambda o: o["at"]):
        total += o["duration"]
        shifts.append({"from_source_s": o["at"], "add_s": round(total, 3)})
    out = {
        "generated_by": "scripts/stop_map.py",
        "master": str(MASTER),
        "silence_threshold_db": SILENT_DB,
        "finding": "Suno paused only the vocal; the mix plays through every gap, so E makes all four stops.",
        "stops": stops,
        "ops_source_time": ops,
        "source_to_edit": {"rule": "edit_t = source_t + add_s of the last shift with from_source_s <= source_t "
                                   "(an insert at t shifts audio from t onward)",
                           "shifts": shifts},
        "edit_duration_s": round(len(x) / sr + total, 3),
    }
    json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)

    # Preview: apply the mutes with short ramps, then the inserts, latest first so earlier times stay valid.
    y = x.copy()
    ramp = int(FADE * sr)
    for o in ops:
        if o["op"] != "mute":
            continue
        i, j = int(o["start"] * sr), int(o["end"] * sr)
        y[i:j] = 0
        y[i - ramp:i] *= np.linspace(1, 0, ramp)[:, None]
        y[j:j + ramp] *= np.linspace(0, 1, ramp)[:, None]
    for o in sorted((o for o in ops if o["op"] == "insert_silence"), key=lambda o: -o["at"]):
        i = int(o["at"] * sr)
        if y[i - ramp:i].any():
            y[i - ramp:i] *= np.linspace(1, 0, ramp)[:, None]
        y = np.concatenate([y[:i], np.zeros((int(o["duration"] * sr), y.shape[1])), y[i:]])
    sf.write(PREVIEW, y, sr, subtype="PCM_24")

    for sid, s in stops.items():
        print(f"{sid}: vocal gap {s['vocal_gap_s']:.2f} s, mix {s['mix_db_in_gap']['min']}..{s['mix_db_in_gap']['max']} dB, "
              f"real silence {s['real_silence_s']:.2f} s -> made silence {s['silence_s']:.2f} s "
              f"(mute {s['edit']['mute'][1] - s['edit']['mute'][0]:.2f} + insert {s['edit']['insert_s']:.2f})")
    print(f"edit duration {out['edit_duration_s']} s; preview {PREVIEW}")


if __name__ == "__main__":
    main()
