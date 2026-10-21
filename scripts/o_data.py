"""O: bake everything the overlay page needs into overlays/data/o_data.js (window.O).

  lines      the sung lines and words (timing/timing_map.json), song time
  stops, failures, half_beat
  vocal      the vocal stem's level per frame (0-1, 24 fps, song time), so the F1 caption jitters with the voice
  surfaces   per shot: each tracked surface (takes/o/tracks/, from scripts/o_track.py) with its quads scaled to the
             overlay stage (take pixels x STAGE_SCALE), text and style
  screen     the screen-space texts (config/o.json "screen")
  chat       S35's planning-chat recording: the chat's opening exchange (docs/planning_chat/planning_chat.md, the
             messages in config/o.json "chat"), as Markdown

Usage: .venv/bin/python scripts/o_data.py
"""
import json
import re
from pathlib import Path

import librosa
import numpy as np

CFG = json.load(open("config/o.json"))
TM = json.load(open("timing/timing_map.json"))
FMAP = json.load(open("timing/failure_map.json"))["regions"]
TIMES = json.load(open("timing/shot_times.json"))["shots"]
VOCAL = "audio/stems/Folks Like Us (Vocals).wav"
OUT = Path("overlays/data/o_data.js")
FPS = 24
STAGE_SCALE = 1.5  # takes are 1280x704 (verticals 704x1280); the surface stage is 1920x1056 (1056x1920);
# config "stage_scale" overrides it per shot (S17's insert is a 1920x1088 still)


def vocal_envelope():
    y, sr = librosa.load(VOCAL, sr=22050, mono=True)
    hop = sr // FPS
    rms = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop, center=True)[0]
    return np.round(np.clip(rms / np.percentile(rms, 98), 0, 1), 3).tolist()


def chat_messages():
    """The planning chat's messages by number: role, time and Markdown text."""
    md = Path("docs/planning_chat/planning_chat.md").read_text()
    out = {}
    for m in re.finditer(r"^## (\d+)\. (User|Claude) \(([^)]+)\)\n(.*?)(?=^---$|\Z)", md, re.S | re.M):
        out[int(m[1])] = {"role": m[2], "time": m[3], "text": m[4].strip()}
    return out


def main():
    lines = [{"text": l["text"], "start": l["start"], "end": l["end"],
              "words": [{"w": w["w"], "start": w["start"], "end": w["end"]} for w in l["words"]]}
             for s in TM["sections"] for l in s["lines"]]
    surfaces = {}
    for s in CFG["surfaces"]:
        tr = json.load(open(f"takes/o/tracks/{s['shot']}__{s['name']}.json"))
        w, h = tr["size"]
        k = CFG.get("stage_scale", {}).get(s["shot"], STAGE_SCALE)
        sh = surfaces.setdefault(s["shot"], {"size": [round(w * k), round(h * k)], "items": []})
        sh["items"].append({"name": s["name"], "text": s["text"], "style": s["style"], "blur": s.get("blur", 0.6),
                            "quads": [[[round(x * k, 1), round(y * k, 1)] for x, y in q]
                                      for q in tr["quads"]]})
    data = {"fps": FPS, "lines": lines, "stops": TM["stops"],
            "failures": {k: {"start": v["start"], "end": v["end"]} for k, v in FMAP.items()},
            "shots": {k: {"start": v["start"], "end": v["end"]} for k, v in TIMES.items()},
            "vocal": vocal_envelope(), "surfaces": surfaces, "screen": CFG["screen"],
            "chat": {**CFG["chat"], "messages": [chat_messages()[n] for n in CFG["chat"]["messages"]]}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.O = " + json.dumps(data, ensure_ascii=False) + ";\n")
    print(f"{OUT}: {len(lines)} lines, {sum(len(v['items']) for v in surfaces.values())} surfaces in "
          f"{len(surfaces)} shots, {len(data['vocal'])} vocal frames")


if __name__ == "__main__":
    main()
