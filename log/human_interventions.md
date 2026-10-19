# Human interventions

Append-only. Every human action: timestamp, what was done, and why (brief, "Production rules").

## 1. 2026-10-15T04:53:10Z (Suno's created_at; logged retroactively) — Suno one-shot

- **What:** A human generated the track in Suno and chose it.
- **Take:** clip `5dbb89c9-7a04-4a80-8798-a06dba4a37f1`, shared as https://suno.com/s/WBFA5UlgX7HMQVUm. Model v6 (`chirp-hawk`), 141.2 s, batch index 0, not a remix, no persona, not instrumental. Settings: `control_sliders: {"aug_creativity": 1}`, no other sliders and no exclusions recorded.
- **Lyrics:** `log/prompts/suno/lyrics_submitted.txt`. These are the planning chat's v2 lyrics (message 8) verbatim, including the bracketed stage directions ("[hard stop, one beat of silence]") and "(points off-screen to an empty chair)".
- **Style prompt:** `log/prompts/suno/style_prompt_submitted.txt`. It is a longer rewrite of the chat's v2 prompt, adding "powerful full-voice belt", "slapback echo", "crisp hard stops and brief silence gaps" and "ending with a fast mumbled disclaimer". The record doesn't say who rewrote it (the human, or Suno's prompt enhancer).
- **Source:** the full clip record, `log/prompts/suno/clip_5dbb89c9.json`, extracted from the share page (`node scripts/fetch_suno.mjs https://suno.com/s/WBFA5UlgX7HMQVUm <out>`). Rejected takes aren't visible from the share page.
- **Evidence:** `audio/track/Folks Like Us.wav` (48 kHz 16-bit stereo, 141.2 s, sha256 `305cbc0c8226b3a3…`), mtime 2026-10-15T01:04 local in `~/Downloads`.
- **Why:** The agent has no access to Suno.

## 2. 2026-10-18 (folder date; logged retroactively) — Mastering run through music-deslop

- **What:** A human ran the Suno WAV through music-deslop M6f 10k twice, with and without the fallback, and supplied both outputs with `REPORT.md` and `fallback.json` (`~/Downloads/music-deslop-m6f-10k-2026-10-18/`).
- **Input:** byte-identical to `audio/track/Folks Like Us.wav` (`~/Downloads/e2e-eval/folks-like-us-suno.wav`, same sha256).
- **Why:** The brief's artifact policy needs the master with artifact suppression off.

## 3. 2026-10-19T12:05–12:08 — Inputs supplied and the master chosen

- **What:** A human:
  - downloaded the stems zip (10 stems, WAV/MP3/MIDI; mtime 12:05) and gave the Suno share link;
  - gave the planning chat share, https://claude.ai/share/7268f962-e815-4237-b079-564cd6fd8ebd;
  - chose the **no-fallback** master ("use the no-fallback option");
  - said the Read-Only project isn't done yet, so its workflows and Blender scripts aren't available.
- **Why:** Inputs listed in the brief. The choice of master is a judgement on the audio (approve/reject).
