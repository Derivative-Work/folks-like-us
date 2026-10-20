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

## 4. 2026-10-19T12:16 — Swap enlarged to 32 GB

- **What:** The human told the agent to enlarge swap to 32 GB and carry on with pre-production. The agent ran the commands (production log, same time).
- **Why:** This box has 38 GB of RAM and had 4 GB of swap. FLUX.2 and LTX-2.3 offload weights to system RAM.

## 5. 2026-10-19, by 12:31 — Timing map spot check by ear

- **What:** The human watched `renders/check/timing_check.mp4` and judged the five cues in `timing/spot_check.md` all good: ST1–ST4's swerve words and "written" at the start of F2. They also confirmed that "And out past", "Gonna", "We" and "all" are sung as written ("cues all good, words sung as written").
- **Why:** Brief, pre-production step 1: "[H] spot-checks five cues by ear."

## 6. 2026-10-19, by 12:35 — Made silences rejected

- **What:** The human listened to `audio/master/preview_stops.wav` and rejected the made silences: "don't inject stops -- they don't sound right. reflow the video around them being missing."
- **Why:** Approve/reject on the audio. The preview is kept as `audio/master/preview_stops_rejected.wav`.

## 7. 2026-10-19, by 12:35 — Failure regions confirmed by ear

- **What:** The human played the A/B clips in `timing/failure_clips/` (no-fallback against with-fallback, per region) and confirmed the artifacts are audible: "yes, I can hear the artifacts". This includes F1, where the measured change is only 59 dB under the music.
- **Why:** Brief, pre-production step 2: "[H] confirms every boundary by ear."

## 8. 2026-10-19, by 12:37 — Cold open: F1 glitch saved for the final chorus

- **What:** The human answered the brief's last open item: "save the F1 glitch for the final chorus".
- **Why:** A creative decision the brief left open for the human.

## 9. 2026-10-19, by 13:01 — Blender contact sheet approved

- **What:** The human reviewed `renders/b/contact_sheet.png` (25 B shots: camera, building stage and continuity) and approved it: "approved, go ahead with the reference stills".
- **Why:** Brief, review checkpoint "[H] Blender contact sheet: every shot's camera, building stage and continuity parameters".

## 10. 2026-10-19, by 13:41 — Reference stills approved

- **What:** The human reviewed the review grids (`takes/stills/review_*.png`) and accepted the agent's recommended pick for each of the seven items: "all yours, go ahead".
- **Why:** Brief, step 6: "[H] approves each sheet".

## 11. 2026-10-19, by 20:05 — Keyframe picks reviewed: redo requested

- **What:** The human reviewed `takes/keyframes/picks_contact_sheet.png` and asked for the six flagged shots (S06, S12, S13, S26, S28a, S29) and the porch shots (S15, S22, S33) to be redone. They also found problems the agent had missed: S28b's water tank is spherical; in S31 the pie and mug intersect the rail; S05's corn still looks like the Blender render, and its flag floats in midair instead of hanging from the pole; S27e's leash hangs at an angle instead of straight down.
- **Why:** Brief: [H] approves or rejects takes. Four of these traced to the Blender set kit (`scripts/blender/build_town.py`): the flag pole leaned into the house with the flag placed apart from it, the pie and mug were placed 4 cm into an 8 cm rail, the tank was a sphere, and the leash was a rigid rod at 60 degrees. All four were fixed at the source and the affected layouts re-rendered (v7).

## 12. 2026-10-20 — Keyframe picks approved except S31

- **What:** The human reviewed the updated `takes/keyframes/picks_contact_sheet.png` (v7–v9) and accepted the picks and the four flags ("Those are fine"). They rejected S31: the pie looks like a dog bowl, and they traced it to the model, which gets narrower toward the top instead of wider.
- **Why:** Brief: [H] approves or rejects takes. The diagnosis was right: in `scripts/blender/build_town.py` the tin tapered from 14 cm at the base to 12 cm at the top, with the crust tapering inside it. The tin now flares from a 19 cm base to a 23 cm rim with a lip, and the pie domes just above it. S31 and S31v layouts re-rendered and keyframes re-made (v8).

## 13. 2026-10-20 — S31 and S31v approved; keyframe stage closed

- **What:** The human reviewed the re-made S31 and S31v keyframes (`takes/keyframes/S31_v8_picks.png`) and approved them: "They're good, go ahead".
- **Why:** Brief: [H] approves or rejects takes. All 29 V keyframes are now approved (`config/keyframe_picks.json`); production moves to V.

## 14. 2026-10-20 — The kid always faces away from the camera

- **What:** The human asked that every shot of the child show them facing away from the camera.
- **Why:** A content rule for the invented kid. Both kid keyframes already comply (S13 v8 s2002 and S27b v4 s2002 show the kid from behind, no face). The V prompts for S13 and S27b state it ("seen from behind, back to the camera"), and the kid's V takes are checked for it.

## 15. 2026-10-20 — S06 V takes rejected: Blender corn

- **What:** The human restarted Claude Code with `CLAUDE_CODE_DISABLE_BG_SHELL_PRESSURE_REAP=1` so long ComfyUI batches aren't stopped by the memory guard, and rejected both S06 V takes: the corn is still the Blender render.
- **Why:** Brief: [H] approves or rejects takes. The cause was the S06 keyframe (v7), whose prompt only said "cornfield beyond"; V keeps its first frame's look. The keyframe was re-made (v8, s2002, real corn) and S06's V takes regenerated from it.

## 16. 2026-10-20 — V picks reviewed: S12, S17, S19 rejected

- **What:** The human watched the V picks reels and rejected three: "S12's walking is very unnatural, and the corn is straight Blender", "S17 seems to be missing motion", "S19's hand is off".
- **Why:** Brief: [H] approves V takes from playback. The three were remade with a weaker depth guide so the people aren't held to their rigid Blender stand-ins, S12 from a new real-corn keyframe (v8 s2002); see the production log. The other 26 picks await the human's verdict.

## 17. 2026-10-20 — S17 fades in and out

- **What:** The human saw the redone S17 fade in and out and asked whether it was intentional.
- **Why:** It wasn't: every chained clip dimmed on its own. S17 was regenerated with steady light (seed 1 picked) and the single dim moved to a grade in E on the second "pie!"; see the production log.

## 18. 2026-10-20 — S17's kitchen dim cut

- **What:** The human watched the S17 preview with the single graded dim on "pie!" against the song and rejected it: "the dimming does not work in context. Remove it".
- **Why:** Brief: [H] judges anything that needs moving pictures. S17 now has no dim; logged in `log/decisions.md` as a cut from the brief.

## 19. 2026-10-20 — V picks approved; V stage closed

- **What:** The human approved all 29 V picks from playback (`config/v_picks.json`), including the redone S12, S17 (no dim) and S19: "Yes, they're good, keep going".
- **Why:** Brief checkpoint: "[H] V and L takes approved shot by shot, from frame grabs and playback". The picked takes' log rows are marked kept; the approved keyframe rows still marked candidate are marked kept too. Production moves to L.

## 20. 2026-10-20 — L picks approved; L stage closed

- **What:** The human watched the L reels with the song and approved all eight picks (`config/l_picks.json`): "The sync is good and these are uncanny in just the right way for the video. Keep going".
- **Why:** Brief checkpoint: "[H] V and L takes approved shot by shot, from frame grabs and playback". The picks' log rows are marked kept. Production moves to G.

## 21. 2026-10-20 — S32 keeps the freeze; O starts

- **What:** The human asked whether the glitch takes should show visible singing. S29 and S29v do (they are the lip-synced takes); S32 is the brief's frozen smile over the sung disclaimer, and S33 is instrumental. The human: "got it, keep the freeze and move on to O".
- **Why:** Brief: [H] judges moving pictures. The G passes stand as made; their check is at the rough cut.
