"""Write the main video's SRT captions from timing/timing_map.json, with the same line windows as the burned-in
captions in overlays/folks.js (a line shows from 0.15 s before its first word until 0.15 s before the next line, or
0.8 s after its last word, whichever is first), in video time: the cold open (config/edit.json "cold_open", song
frames, clipped to its span) and then the song. The text is the lyric as sung, without the on-screen swaps. One sound
cue marks the data center's hum once the song has stopped (config/edit.json "hum", until the S33 hold ends). The cards
after it carry their own text.

Usage: .venv/bin/python scripts/export_srt.py  ->  deliverables/folks_like_us.en.srt
"""
import json
from pathlib import Path

FPS = 24
CFG = json.load(open("config/edit.json"))
TM = json.load(open("timing/timing_map.json"))
LINES = [l for s in TM["sections"] for l in s["lines"]]
SONG_END = 3389  # song frames in the main cut (scripts/e_edit.py segments_main)


def stamp(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def windows():
    """(start, end, text) per sung line, in song time, as the overlay shows them."""
    for i, l in enumerate(LINES):
        nxt = LINES[i + 1]["start"] if i + 1 < len(LINES) else None
        yield l["start"] - 0.15, min(nxt - 0.15, l["end"] + 0.8) if nxt is not None else l["end"] + 0.8, l["text"]


def main():
    a, b = (f / FPS for f in CFG["cold_open"]["song_frames"])
    cold = b - a
    cues = [(max(s, a) - a, min(e, b) - a, text) for s, e, text in windows() if e > a and s < b]
    cues += [(s + cold, e + cold, text) for s, e, text in windows()]
    hum_end = SONG_END + CFG["bookends"]["S33_tail"]
    cues.append((CFG["hum"]["start_song_s"] + cold, hum_end / FPS + cold, "[A data center hums]"))
    out = [f"{i + 1}\n{stamp(s)} --> {stamp(e)}\n{text}\n" for i, (s, e, text) in enumerate(cues)]
    dst = Path("deliverables/folks_like_us.en.srt")
    dst.parent.mkdir(exist_ok=True)
    dst.write_text("\n".join(out))
    print(dst, len(out), "cues")


if __name__ == "__main__":
    main()
