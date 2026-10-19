"""Pre-production step 3: measure each stop in the mix and write timing/stops.json.

Measured: the master's level in each stop's vocal gap (from the timing map). Suno paused only the vocal; the band
plays through every gap, so the take never goes silent. No silence is made either: [H] heard made silences
(mute + inserted beats) and rejected them (log/human_interventions.md, entry 6). The shots play over the vocal gaps,
and the edit keeps the take's timing: edit time = source time.

Usage: .venv/bin/python scripts/stop_map.py  ->  timing/stops.json
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf

MASTER = Path("audio/master/folks_like_us_master_nofallback.wav")
TIMING = Path("timing/timing_map.json")
OUT = Path("timing/stops.json")
SILENT_DB = -60.0  # mix level that counts as silence (50 ms RMS frames)


def frames_db(x, sr, frame_s=0.05):
    h = int(sr * frame_s)
    n = len(x) // h
    m = x[: n * h].reshape(n, h, -1)
    return 20 * np.log10(np.sqrt((m ** 2).mean(axis=(1, 2))) + 1e-12)


def longest_run(mask):
    best = run = 0
    for v in mask:
        run = run + 1 if v else 0
        best = max(best, run)
    return best


def main():
    x, sr = sf.read(MASTER, dtype="float64", always_2d=True)
    tm = json.load(open(TIMING))
    db = frames_db(x, sr)
    stops = {}
    for sid, c in tm["stops"].items():
        a, b = c["before"]["end"], c["after"]["start"]
        seg = db[int(a / 0.05):max(int(b / 0.05), int(a / 0.05) + 1)]
        stops[sid] = {
            "section": c["section"], "setup_word": c["before"], "swerve_word": c["after"],
            "vocal_gap": [a, b], "vocal_gap_s": c["gap_s"],
            "mix_db_in_gap": {"min": round(float(seg.min()), 1), "max": round(float(seg.max()), 1)},
            "real_silence_s": round(longest_run(seg < SILENT_DB) * 0.05, 2),
        }
    out = {
        "generated_by": "scripts/stop_map.py",
        "master": str(MASTER),
        "silence_threshold_db": SILENT_DB,
        "finding": "Suno paused only the vocal; the band plays through every stop, so the take never goes silent.",
        "edit": "No silence is made ([H] rejected made silences, 2026-10-19). The stop gags play over the vocal "
                "gaps; edit time = source time.",
        "stops": stops,
    }
    json.dump(out, open(OUT, "w"), indent=1, ensure_ascii=False)
    for sid, s in stops.items():
        print(f"{sid}: vocal gap {s['vocal_gap'][0]:.2f}-{s['vocal_gap'][1]:.2f} ({s['vocal_gap_s']:.2f} s), "
              f"mix {s['mix_db_in_gap']['min']}..{s['mix_db_in_gap']['max']} dB, real silence {s['real_silence_s']:.2f} s")


if __name__ == "__main__":
    main()
