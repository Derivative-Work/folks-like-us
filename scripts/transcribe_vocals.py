"""Pre-production step 1a: transcribe the vocals stem with WhisperX (word timestamps) to find what is actually sung.

The transcript is evidence for lyrics/as_sung.txt, not the lyrics: Whisper mishears sung words. timing_map.py
force-aligns the as-sung lyrics, not this transcript.
Usage: .venv/bin/python scripts/transcribe_vocals.py [model=large-v3]  ->  timing/whisper_words.json
"""
import json
import sys
from pathlib import Path

import whisperx

STEM = "audio/stems/Folks Like Us (Vocals).wav"
OUT = Path("timing/whisper_words.json")

model_name = sys.argv[1] if len(sys.argv) > 1 else "large-v3"
audio = whisperx.load_audio(STEM)
# No VAD trimming of quiet passages: the stops and the mumbled disclaimer are what we're looking for.
model = whisperx.load_model(model_name, "cuda", compute_type="float16", language="en",
                            asr_options={"beam_size": 5, "condition_on_previous_text": False})
result = model.transcribe(audio, batch_size=8, language="en")
align_model, meta = whisperx.load_align_model(language_code="en", device="cuda")
result = whisperx.align(result["segments"], align_model, meta, audio, "cuda", return_char_alignments=False)

out = []
for s in result["segments"]:
    print(f"[{s['start']:7.2f} - {s['end']:7.2f}] {s['text'].strip()}")
    out.append({"start": round(s["start"], 3), "end": round(s["end"], 3), "text": s["text"].strip(),
                "words": [{"w": w["word"], "start": round(w.get("start", -1), 3), "end": round(w.get("end", -1), 3),
                           "score": round(w.get("score", 0), 3)} for w in s["words"]]})
OUT.parent.mkdir(exist_ok=True)
json.dump({"model": model_name, "stem": STEM, "whisperx": whisperx.__version__ if hasattr(whisperx, "__version__") else None,
           "segments": out}, open(OUT, "w"), indent=1)
