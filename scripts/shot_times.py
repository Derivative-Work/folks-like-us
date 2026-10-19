"""Resolve every song shot's start cue (config/shot_cues.json) to a time and frame: timing/shot_times.json.

A cue is "Section|line|word" (the word's start), "end:Section|line|word" (its end), "mid:Section|line|word"
(its middle: a held note's tail, when the next word follows without a gap), "t:<seconds>", or "section:<name>" (the
section's start). Words are indexed as in lyrics/as_sung.txt, from 0. Each shot ends where the
next one starts; the last ends at the music's end. Edit time = source time (no made stops). Frames are at 24 fps.

Usage: .venv/bin/python scripts/shot_times.py  ->  timing/shot_times.json
"""
import json
from pathlib import Path

CUES = Path("config/shot_cues.json")
TIMING = Path("timing/timing_map.json")
OUT = Path("timing/shot_times.json")
FPS = 24


def resolve(cue, tm):
    if cue.startswith("t:"):
        return float(cue[2:]), cue
    if cue.startswith("section:"):
        sec = next(s for s in tm["sections"] if s["name"] == cue[8:])
        return sec["start"], cue
    kind, _, ref = cue.partition(":") if cue[:4] in ("end:", "mid:") else ("start", "", cue)
    section, line, word = ref.split("|")
    sec = next(s for s in tm["sections"] if s["name"] == section)
    w = sec["lines"][int(line)]["words"][int(word)]
    t = {"start": w["start"], "end": w["end"], "mid": (w["start"] + w["end"]) / 2}[kind]
    label = {"start": "", "end": "end of ", "mid": "middle of "}[kind]
    return t, f"{label}{w['w']!r} ({section})"


def main():
    tm = json.load(open(TIMING))
    cues = json.load(open(CUES))["shots"]
    starts = [(sid, *resolve(c, tm)) for sid, c in cues.items()]
    if [t for _, t, _ in starts] != sorted(t for _, t, _ in starts):
        raise SystemExit("shot cues are out of order")
    music_end = tm["events"]["music_end"]
    out = {}
    for i, (sid, t, word) in enumerate(starts):
        end = starts[i + 1][1] if i + 1 < len(starts) else music_end
        out[sid] = {"start": round(t, 3), "end": round(end, 3), "duration": round(end - t, 3),
                    "start_frame": round(t * FPS), "end_frame": round(end * FPS), "cue": word}
    json.dump({"generated_by": "scripts/shot_times.py", "fps": FPS, "time": "source = edit (no made stops)",
               "shots": out}, open(OUT, "w"), indent=1, ensure_ascii=False)
    for sid, s in out.items():
        print(f"{sid}: {s['start']:7.2f}-{s['end']:7.2f} ({s['duration']:5.2f} s, frames {s['start_frame']}-"
              f"{s['end_frame']})  {s['cue']}")


if __name__ == "__main__":
    main()
