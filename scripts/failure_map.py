"""Pre-production step 2: write timing/failure_map.json and listening clips for [H] to confirm F1-F3 by ear.

The boundaries come from the mastering model's own log (docs/mastering/fallback.json: where its fallback faded the
model's change out). Inside a region the no-fallback master is the model's failing output and the with-fallback
master is (nearly) the input, so their difference is the artifact alone. Its level per region, against the master's
and against the difference everywhere else (which should be silence), checks the log against the audio.
Clips (timing/failure_clips/, git-ignored): for each region, 3 s before its start to 3 s after its end, as
  F<n>_nofallback.wav  (the master we use), F<n>_withfallback.wav  (clean), F<n>_artifact.wav  (their difference).

Usage: .venv/bin/python scripts/failure_map.py  ->  timing/failure_map.json, timing/failure_clips/
"""
import json
from pathlib import Path

import numpy as np
import soundfile as sf

NOFB = Path("audio/master/folks_like_us_master_nofallback.wav")
WITHFB = Path("audio/master/with-fallback/folks_like_us_master_withfallback.wav")
FALLBACK = Path("docs/mastering/fallback.json")
TIMING = Path("timing/timing_map.json")
OUT = Path("timing/failure_map.json")
CLIPS = Path("timing/failure_clips")
PAD = 3.0


def db(x):
    return round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)), 1)


def words_in(tm, a, b):
    return [w["w"] for s in tm["sections"] for l in s["lines"] for w in l["words"] if w["end"] > a and w["start"] < b]


def main():
    nofb, sr = sf.read(NOFB, dtype="float64")
    withfb, sr2 = sf.read(WITHFB, dtype="float64")
    assert sr == sr2 and nofb.shape == withfb.shape
    diff = nofb - withfb
    tm = json.load(open(TIMING))
    song = next(s for s in json.load(open(FALLBACK)) if s["song"] == "folks-like-us")
    CLIPS.mkdir(parents=True, exist_ok=True)
    # Everything outside all regions and their 0.5 s fades: where the two masters should match.
    clean = np.ones(len(diff), bool)
    for a, b, _ in song["regions"]:
        clean[max(0, int((a - 0.5) * sr)):int((b + 0.5) * sr)] = False
    regions = {}
    for i, (a, b, gain) in enumerate(song["regions"], 1):
        name = f"F{i}"
        ia, ib = int(a * sr), int(b * sr)
        regions[name] = {
            "start": round(a, 3), "end": round(b, 3), "duration": round(b - a, 3),
            "deepest_fade": round(1 - gain, 3),
            "words": " ".join(words_in(tm, a, b)),
            "master_db": db(nofb[ia:ib]), "artifact_db": db(diff[ia:ib]),
            "artifact_to_master_db": round(db(diff[ia:ib]) - db(nofb[ia:ib]), 1),
            "confirmed_by_ear": None,
        }
        ca, cb = max(0, ia - int(PAD * sr)), min(len(nofb), ib + int(PAD * sr))
        for tag, x in (("nofallback", nofb), ("withfallback", withfb), ("artifact", diff)):
            sf.write(CLIPS / f"{name}_{tag}.wav", x[ca:cb], sr, subtype="PCM_24")
        regions[name]["clip_offset_s"] = round(ca / sr, 3)
    fm = {
        "generated_by": "scripts/failure_map.py",
        "source": f"{FALLBACK} (music-deslop M6f 10k fallback regions: per-bin gain jitter rising above 0.4 dB)",
        "master": str(NOFB),
        "status": "boundaries from the model's log; [H] confirms each by ear (confirmed_by_ear)",
        "difference_outside_regions_db": db(diff[clean]),
        "regions": regions,
    }
    json.dump(fm, open(OUT, "w"), indent=1, ensure_ascii=False)
    for k, r in regions.items():
        print(f"{k}: {r['start']:.3f}-{r['end']:.3f} ({r['duration']:.2f} s), artifact {r['artifact_db']} dB, "
              f"{r['artifact_to_master_db']} dB under the master; words: {r['words'] or '(none)'}")
    print(f"difference outside the regions: {fm['difference_outside_regions_db']} dB")


if __name__ == "__main__":
    main()
