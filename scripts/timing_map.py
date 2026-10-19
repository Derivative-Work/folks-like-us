"""Pre-production step 1: build timing/timing_map.json from the Suno take.

- Words: WhisperX forced alignment (wav2vec2, English) of lyrics/as_sung.txt against the vocals stem, one lyric line
  per alignment segment. Each line's window runs from the previous line's last transcribed word to the next line's
  first, using the WhisperX transcript (timing/whisper_words.json, scripts/transcribe_vocals.py) as anchors, so a
  word Whisper missed ("Gonna", "We") still gets a window.
- Beats: librosa beat tracking on the drums + percussion stems; downbeat phase = the beat offset (mod 4) with the
  strongest low-band onset energy (4/4 assumed).
- Stops (ST1-ST4): the cue words around each stop in the lyrics. stops.json (step 3) measures the silences.
- Failure regions (F1-F3): candidates from the mastering model's fallback log (docs/mastering/fallback.json), not
  yet confirmed by ear.
- Also writes timing/as_sung_lines.srt and timing/as_sung_words.srt to check sync by playing the master with them.

Usage: .venv/bin/python scripts/timing_map.py  ->  timing/timing_map.json, timing/*.srt
"""
import difflib
import hashlib
import json
import re
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import whisperx

TRACK = Path("audio/track/Folks Like Us.wav")
MASTER = Path("audio/master/folks_like_us_master_nofallback.wav")
STEMS = Path("audio/stems")
LYRICS = Path("lyrics/as_sung.txt")
TRANSCRIPT = Path("timing/whisper_words.json")
FALLBACK = Path("docs/mastering/fallback.json")
OUT = Path("timing/timing_map.json")
SR_BEAT = 22050
HOP = 512
# (stop, section, last word before the stop, first word after it); words as written in lyrics/as_sung.txt.
STOPS = [("ST1", "Verse 1", "data—", "—day."),
         ("ST2", "Chorus", "sky—", "It's"),
         ("ST3", "Verse 2", "but—", "—you!"),
         ("ST4", "Final chorus", "sky—", "It's")]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def stem(name):
    return STEMS / f"Folks Like Us ({name}).wav"


def norm(word):
    return re.sub(r"[^a-z']", "", word.lower().replace("’", "'"))


def parse_lyrics():
    """Sections: [{name, note, lines: [text]}]."""
    sections = []
    for raw in LYRICS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"\[(.+?)\]\s*(?:\((.+)\))?$", line)
        if m:
            sections.append({"name": m.group(1), "note": m.group(2), "lines": []})
        else:
            sections[-1]["lines"].append(line)
    return sections


def line_windows(lines, transcript_words, duration):
    """For each lyric line, a (start, end) window from the transcript anchors around it."""
    lyric_tokens = [(i, norm(w)) for i, text in enumerate(lines) for w in text.split()]
    trans = [w for w in transcript_words if w["start"] >= 0]
    sm = difflib.SequenceMatcher(a=[t for _, t in lyric_tokens], b=[norm(w["w"]) for w in trans], autojunk=False)
    first, last = {}, {}
    for a, b, n in sm.get_matching_blocks():
        for k in range(n):
            li = lyric_tokens[a + k][0]
            w = trans[b + k]
            first.setdefault(li, w["start"])
            last[li] = w["end"]
    missing = [i for i in range(len(lines)) if i not in first]
    if missing:
        raise SystemExit(f"no transcript anchor for lines {missing}: {[lines[i] for i in missing]}")
    windows = []
    for i in range(len(lines)):
        start = last[i - 1] + 0.02 if i > 0 else max(0.0, first[i] - 2.0)
        end = first[i + 1] - 0.02 if i + 1 < len(lines) else min(duration, last[i] + 1.0)
        windows.append((start, end))
    return windows


def align_words(sections, duration):
    lines = [text for s in sections for text in s["lines"]]
    transcript = json.load(open(TRANSCRIPT))
    twords = [w for seg in transcript["segments"] for w in seg["words"]]
    windows = line_windows(lines, twords, duration)
    audio = whisperx.load_audio(str(stem("Vocals")))
    model, meta = whisperx.load_align_model(language_code="en", device="cuda")
    segments = [{"start": a, "end": b, "text": text} for text, (a, b) in zip(lines, windows)]
    # whisperx.align splits segments into sentences ("—day. A brand new day." becomes two), so regroup its words
    # by lyric line. Each sentence still aligns inside its line's window.
    aligned = whisperx.align(segments, model, meta, audio, "cuda", return_char_alignments=False)["segments"]
    flat = [w for seg in aligned for w in seg["words"]]
    if [w["word"] for w in flat] != [w for text in lines for w in text.split()]:
        raise SystemExit("aligned words differ from the lyrics")
    out, k, pos = [], 0, 0
    for s in sections:
        sec = {"name": s["name"], "note": s["note"], "lines": []}
        for text in s["lines"]:
            n = len(text.split())
            words = [{"w": w["word"], "start": round(w["start"], 3), "end": round(w["end"], 3),
                      "score": round(w.get("score", 0.0), 3)} for w in flat[pos:pos + n]]
            pos += n
            sec["lines"].append({"text": text, "start": words[0]["start"], "end": words[-1]["end"],
                                 "window": [round(windows[k][0], 3), round(windows[k][1], 3)], "words": words})
            k += 1
        out.append(sec)
    return out


def vocal_db(frame_s=0.02):
    x, sr = sf.read(stem("Vocals"))
    x = x.mean(axis=1) if x.ndim > 1 else x
    hop = int(sr * frame_s)
    n = len(x) // hop
    return 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-12)


def refine(sections, frame_s=0.02, below_median_db=10.0, gap_s=0.25):
    """Correct the aligner where sung audio fools it, using the vocals stem's level (20 ms frames).

    wav2vec2 places word starts well but not the ends of held notes: a word before a pause either stops early
    (the held "sky—") or runs to the window's edge ("pie!"). And after a stop it can start a word in the silence.
    - start: if the voice is quiet there, move it to the first onset (3 frames above the threshold) before its end;
    - end, for a word followed by a gap of gap_s or more: the first 100 ms below the threshold, capped at the
      next word's start.
    The threshold is below_median_db under the median level of voiced frames.
    """
    db = vocal_db(frame_s)
    thr = np.median(db[db > -50]) - below_median_db
    loud = db >= thr
    words = [w for s in sections for line in s["lines"] for w in line["words"]]
    f = lambda t: int(round(t / frame_s))
    for i, w in enumerate(words):
        a, b = f(w["start"]), f(w["end"])
        if not loud[a:a + 3].all():
            onset = next((k for k in range(a, b) if loud[k:k + 3].all()), None)
            if onset is not None:
                w["start_aligner"], w["start"] = w["start"], round(onset * frame_s, 3)
        nxt = words[i + 1]["start"] if i + 1 < len(words) else len(db) * frame_s
        if nxt - w["end"] >= gap_s or (w["end"] - w["start"] > 1.5 and nxt - w["end"] < 0.05):
            k = f(w["start"] + 0.1)
            while k < f(nxt) and loud[k:k + 5].any():
                k += 1
            w["end_aligner"], w["end"] = w["end"], round(min(k * frame_s, nxt), 3)
    for s in sections:
        for line in s["lines"]:
            line["start"], line["end"] = line["words"][0]["start"], line["words"][-1]["end"]
    return round(float(thr), 1)


def beats():
    y = sum(librosa.load(stem(n), sr=SR_BEAT, mono=True)[0] for n in ("Drums", "Percussion"))
    tempo, frames = librosa.beat.beat_track(y=y, sr=SR_BEAT, hop_length=HOP, start_bpm=84, units="frames")
    times = librosa.frames_to_time(frames, sr=SR_BEAT, hop_length=HOP)
    low = librosa.onset.onset_strength(y=librosa.effects.preemphasis(y, coef=-0.97), sr=SR_BEAT, hop_length=HOP,
                                       fmax=200)
    strength = [low[frames[p::4]].sum() for p in range(4)]
    phase = int(np.argmax(strength))
    return float(np.atleast_1d(tempo)[0]), phase, [round(float(t), 3) for t in times], \
        [round(float(t), 3) for t in times[phase::4]]


def music_end(path, floor_db=-60.0):
    """Last time the master is above floor_db (50 ms RMS frames)."""
    x, sr = sf.read(path)
    x = x.mean(axis=1) if x.ndim > 1 else x
    hop = sr // 20
    n = len(x) // hop
    db = 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-12)
    loud = np.nonzero(db > floor_db)[0]
    return round(float((loud[-1] + 1) * hop / sr), 3)


def stop_cues(sections):
    cues = {}
    for sid, sec_name, before, after in STOPS:
        sec = next(s for s in sections if s["name"] == sec_name)
        words = [w for line in sec["lines"] for w in line["words"]]
        i = next(i for i, w in enumerate(words) if w["w"] == before)
        if words[i + 1]["w"] != after:
            raise SystemExit(f"{sid}: expected {after!r} after {before!r}, got {words[i + 1]['w']!r}")
        cues[sid] = {"section": sec_name, "before": {"w": before, "end": words[i]["end"]},
                     "after": {"w": after, "start": words[i + 1]["start"]},
                     "gap_s": round(words[i + 1]["start"] - words[i]["end"], 3)}
    return cues


def failure_regions():
    song = next(s for s in json.load(open(FALLBACK)) if s["song"] == "folks-like-us")
    return {f"F{i + 1}": {"start": round(a, 3), "end": round(b, 3), "deepest_fade": round(1 - g, 3),
                          "status": "candidate from fallback.json; not yet confirmed by ear"}
            for i, (a, b, g) in enumerate(song["regions"])}


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for n, (a, b, text) in enumerate(items, 1):
            f.write(f"{n}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n\n")


def main():
    info = sf.info(TRACK)
    duration = round(info.frames / info.samplerate, 3)
    sections = align_words(parse_lyrics(), duration)
    thr = refine(sections)
    tempo, phase, beat_times, downbeats = beats()
    sung = [s for s in sections if s["lines"]]
    for s in sections:
        if s["lines"]:
            s["start"], s["end"] = s["lines"][0]["start"], s["lines"][-1]["end"]
    # The instrumental outro runs from the last sung word to the end of the music.
    for s in sections:
        if not s["lines"]:
            s["start"], s["end"] = sung[-1]["end"], music_end(MASTER)
    tm = {
        "generated_by": "scripts/timing_map.py",
        "audio": {"file": str(TRACK), "sha256": sha256(TRACK), "duration_s": duration, "sample_rate": info.samplerate,
                  "master": str(MASTER), "master_sha256": sha256(MASTER)},
        "alignment": {"method": "whisperx.align (wav2vec2 en), one segment per lyric line",
                      "audio": str(stem("Vocals")), "lyrics": str(LYRICS), "anchors": str(TRANSCRIPT),
                      "refined": f"starts in silence and ends before pauses moved to the vocals stem's level "
                                 f"({thr} dB threshold); originals kept as start_aligner/end_aligner"},
        "tempo_bpm": round(tempo, 2),
        "time_signature": "4/4 (assumed)",
        "downbeat_phase": phase,
        "beats": beat_times,
        "downbeats": downbeats,
        "sections": sections,
        "stops": stop_cues(sections),
        "failures": failure_regions(),
        "events": {"first_vocal": sung[0]["start"], "last_vocal": sung[-1]["end"],
                   "music_end": music_end(MASTER)},
    }
    OUT.parent.mkdir(exist_ok=True)
    json.dump(tm, open(OUT, "w"), indent=1, ensure_ascii=False)
    lines = [line for s in sections for line in s["lines"]]
    write_srt(OUT.parent / "as_sung_lines.srt", [(l["start"], l["end"], l["text"]) for l in lines])
    words = [w for l in lines for w in l["words"]]
    write_srt(OUT.parent / "as_sung_words.srt",
              [(w["start"], max(w["end"], w["start"] + 0.15), w["w"]) for w in words])
    print(f"tempo {tm['tempo_bpm']} bpm, {len(beat_times)} beats, downbeat phase {phase}")
    for s in sections:
        print(f"{s['name']:14s} {s['start']:7.2f}-{s['end']:7.2f}")
    for sid, c in tm["stops"].items():
        print(f"{sid}: {c['before']['w']} ends {c['before']['end']:.2f}, {c['after']['w']} starts "
              f"{c['after']['start']:.2f} (gap {c['gap_s']:.2f} s)")
    low = [(w["w"], w["start"], w["score"]) for w in words if w["score"] < 0.3]
    print(f"{len(words)} words; low alignment score (<0.3): {low}")


if __name__ == "__main__":
    main()
