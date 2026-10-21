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

## 22. 2026-10-20 — Pending [H] screen captures

- **What:** S03 (three seconds of the real Suno generation screen) and S35 (screen recordings of the real FEC filings and of the planning chat) are [H] captures (brief: "H capture, E"). The rough cut carries labelled placeholders in their slots (S03: 3.0 s inside the intro; S35: 8 s after S34).
- **Why:** The agent doesn't make screen captures (brief production rules).

## 23. 2026-10-20 — Rough-cut notes

- **What:** The human watched the rough cut and gave these notes:
  - Hold the first kite shot (S13) longer, eating into the first church shot (S14).
  - Hold the first "AI" plane shot (S16) longer, eating into the apple-pie shot (S17).
  - On the first "don't know a thing about it", start on a crop closer to the face that keeps the pointing hand, then cut straight to the full angle at "don't you ask us".
  - The diner TVs (S20, S23) are not all populated, so the mask is wrong.
  - At "we'll talk about" (S21) the chair's TBD is missing.
  - The final-chorus montage (S27–S28) cuts far too fast. Slow it, off the beat if need be, eating into "It's two little letters" while leaving a few seconds before the hand gag.
  - Combine the spectrogram with the "AI cleanup model couldn't fix…" card.
  - Use https://github.com/Derivative-Work/folks-like-us as the production-log link.
  - After the "AI-generated satire" card, close on a final card along the lines of "note from the human: election day is november 3, 2026. please make a plan to vote".
- **Why:** This is the brief's rough-cut checkpoint. The changes are logged in `log/decisions.md`. The lengthened V takes and the new S19c lip-sync are pending [H].

## 24. 2026-10-20 — TV wall and credit line, from rough cut 2

- **What:** The human watched rough cut 2 and asked for two more changes.
  - "the TVs still aren't quite right". Agent's diagnosis: the chroma key left dark holes where the screens caught glare, and it painted the ads over a diner's dark hair.
  - On the end card, put "Production log" and its URL on a new line, with the URL in a monospace font.
- **Why:** This is the brief's rough-cut checkpoint. The changes are logged in `log/decisions.md`.

## 25. 2026-10-20 — S15's "A I" moved

- **What:** The human: "at the first 'it's two little letters', the 'AI' in the top right is partially obscured by the 'AI-generated satire' disclaimer -- move the 'AI' somewhere else that fits". It now sits in the sky right of the porch post, below the flag pole, a little larger than before (take px 1132–1276 × 270–400).
- **Why:** [H] judges moving pictures; the label stays where it is on every shot.

## 26. 2026-10-20 — S25 cut; the montage gets its time

- **What:** The human said the final-chorus cuts were still too fast: "delete the last 'pointing at empty chair' scene and use the time to give those cuts more time". S25, the ALSO TBD cutaway, is gone, and the 14 frames go to the S27–S28 montage.
- **Why:** [H] judges moving pictures. Logged in `log/decisions.md`.

## 27. 2026-10-20 — Montage from "something" to "and"

- **What:** The human: "shorten the yard shot so the montage starts on 'something', and make the porch shot start on the 'and'". S26 now ends as "something" begins (95.56 s), and S29 starts on the "and" after "letters" (102.35 s).
- **Why:** [H] judges moving pictures. Logged in `log/decisions.md`.

## 28. 2026-10-20 — S33 ending and the hum

- **What:** The human: "the fadeout to the data center only at the end needs to be sooner so it's visible for longer, and make the data center sound louder".
  - S33 now fades everything but the building over 1.5 s, then holds the building alone on black for 2.5 s. It used to fade over the last second, which left it alone for only a few frames.
  - The hum is 10 dB louder.
- **Why:** [H] judges moving pictures and audio.

## 29. 2026-10-20 — Cold open: porch only; S33 ending approved

- **What:** The human: "the new ending is great, but for the opening shot only make it use the porch singing in place of the data center with the leash on the fence".
  - S33's held building is approved.
  - The cold open had picked up the montage's new cuts: the leash at the fence, the church sign and the water tower, which ran over song frames 2392–2456. It now follows the song's shot times, so it is S29's porch take from its first frame, as the brief's hook intends.
- **Why:** [H] judges moving pictures. The S33 row is marked kept.

## 30. 2026-10-20 — The building holds past the song

- **What:** The human: "make the data center bit at the end sit for a second after the song finishes and also delay the fade in by the same amount".
  - S33 runs 24 frames past the song's end, over the hum alone.
  - Its fade to the building starts 24 frames later. The building still holds alone for 2.5 s, now ending 1 s after the song.
- **Why:** [H] judges moving pictures.

## 31. 2026-10-20 — Vote card 10 s; the chat log; S35 from the real FEC pages

- **What:** The human asked for three things:
  - Make the voting reminder 10 s long "so that it doesn't get covered by youtube suggestions".
  - Recover the planning chat: they had clicked "regenerate" on an earlier prompt and can no longer reach it.
  - Retrieve and render the FEC filings, with links to verify them.
- **What the agent did:**
  - The chat was extracted on 2026-10-19, before the regenerate. It is in `docs/planning_chat/` (Markdown and the raw share snapshot) and was sent to the human.
  - The FEC pages were captured from fec.gov. Findings and links are in `docs/fec/README.md`.
  - S35 is now rendered from those pages and the chat, replacing the placeholder.
- **Why:** The human asked the agent to make S35 itself, though the brief makes it an [H] screen capture (logged in `log/decisions.md`). The human still verifies the FEC figures from the links.

## 32. 2026-10-20 — No satire label on the FEC pages; credits centred

- **What:** The human: "I don't think the 'AI-generated satire' belongs on the screen recordings of the actual FEC filings. Make the 'Lyrics by...' through the production log URL section fully horizontally centered rather than being in a block that's centered." The FEC part of S35 now has no label (the planning chat keeps its own), and the fact card's credit lines are each centred.
- **Why:** [H] judges moving pictures; logged in `log/decisions.md`.

## 33. 2026-10-20 — No label on the planning chat either

- **What:** The human: "yes remove it from the planning chat as well". All of S35 is now unlabelled.
- **Why:** [H] judges moving pictures; logged in `log/decisions.md`.

## 34. 2026-10-20 — vote.org on the vote card

- **What:** The human: "also put `vote.org` on the voting reminder page". It sits under "Please make a plan to vote." in the monospace used for the log link, on the main and vertical cards.
- **Why:** The human's own closing note.

## 35. 2026-10-21 — Date on the $55.7M figure

- **What:** The human: "find the date of the $55.7M number and add it to the end screen".
  - The NYT tally is dated Sept. 29, 2026. That comes from its URL, `nytimes.com/interactive/2026/09/29/...`, as cited by AI Weekly's Sept. 30 summary; nytimes.com can't be fetched to confirm it on the page.
  - The fact card's first line now reads "by a New York Times tally of Sept. 29, 2026". The source links are in `docs/fec/README.md`.
- **Why:** This is the brief's fact-card check against sources; the human confirms the date on the Times page.

## 36. 2026-10-21 — S03 screen recording supplied

- **What:** The human recorded Suno: pasting the lyrics and the style prompt, clicking "Create", waiting for the takes to become playable, and playing one. The file is `~/Downloads/Screen Recording 2026-10-20 at 23.31.55.mov`, 43 s at 3074×2118 and 120 fps, copied to `takes/s03/suno_recording.mov` (git-ignored).
  - Per the human, it is a recreation: the song generated in it is not the one in the film.
  - Their note: "you'll probably have to do some cutting and cropping".
- **Why:** The brief's S03 is an [H] capture. This replaces the last placeholder.

## 37. 2026-10-21 — S03 timing

- **What:** The human: "don't use a static image for the 'create' button -- it should be shown spinning. at the cut on the generated songs, don't speed it up too much -- time the spinner and cut out duplicate frames so it only spins maybe twice or three times before it starts to 'play'". Done as logged in `log/decisions.md`.
- **Why:** [H] judges moving pictures.

## 38. 2026-10-21 — S03 dissolves into S04

- **What:** The human: "fade from the suno screen section into the landscape shot". S03's last 12 frames (0.5 s) dissolve into S04, and the label fades in with the landscape.
- **Why:** [H] judges moving pictures.

## 39. 2026-10-21 — Rough cut 2 approved; pushed to GitHub

- **What:** The human, after the S03 dissolve: "everything looks good", and gave access to https://github.com/Derivative-Work/folks-like-us with "push your work there". This approves everything still pending:
  - the lengthened V takes (S13, S16, S27a–e, S28a–b);
  - the L extras S19c and S26x;
  - the G passes, including S33 with its tail;
  - S03 and S35;
  - the rough cut as a whole, which is the brief's rough-cut checkpoint.
- **What changed:** Every log row still marked "pending [H]" now reads "kept" (its output is a current pick in `config/`), "not used" (an alternative [H] didn't pick) or "superseded" (regenerated under the same name). The repository was pushed to GitHub. It is private for now.
- **Why:** This is the brief's rough-cut checkpoint, [H]'s call. The final cut, the delivery resolution and the [H] final checkpoint remain.

## 40. 2026-10-21 — Final cut approved

- **What:** The human checked the upload files: "the files are good". This approves `takes/e/delivery/folks_like_us_youtube_1080p24.mp4` (1080p, 3:15) and `takes/e/delivery/folks_like_us_shorts_1080x1920.mp4` (18.5 s).
- **Why:** This is the brief's final checkpoint, "[H] Final cut, vertical cut, and the fact card re-checked against sources". The fact card's sources and the FEC check are in `docs/fec/README.md`. The human saw both and earlier added the NYT date. Remaining from the brief: the archive.

## 41. 2026-10-21 — README and archive

- **What:** The human: "make the README and then the archive. Suno handle is fine." The Suno handle stays in `log/prompts/suno/`.
- **Why:** The brief's last deliverable is "the full production archive". The README is for viewers arriving from the credits.

## 42. 2026-10-21 — README: mastering credits

- **What:** The human: "the readme needs the part about mastering, particularly the model's attributions (see ghost in the machine's for this)". The README's credits now follow Ghost in the Machine's:
  - music-deslop, built and trained by Claude Code from a human-written spec, on Creative Commons audio only, and private for now;
  - its CC BY 4.0 training datasets with citations (Slakh2100, VocalSet 1.2, CSTR VCTK 0.92);
  - the tools used to degrade the training inputs.
  - Specific to this project: the no-fallback master is used on purpose, so the model's failures stay in. The font links come from each font's licence file.
- **Why:** Attribution for the mastering model's training data.
