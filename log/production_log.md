# Production log

Append-only. One entry per generation, render or action: timestamp, shot ID and stage code where there is one, model and version, prompt, seed, inputs, outputs, kept or rejected, and the command that regenerates it.

## 2026-10-19T11:51:02-04:00 — Setup: repo scaffolding and environment script

- **What:** Read the brief (Claude Doc `S37uBB1UQJGfxSWx7wQ6Ek`, rev 9) in full. Surveyed the box: RTX 5090 32 GB (driver 595.99.02), 38 GB RAM and 4 GB swap, Ubuntu 26.04.1. Blender 5.2.2 LTS, ffmpeg 8.0.1 with libx264, Node v24.22.0 and uv 0.13.0 were already installed, matching Ghost in the Machine. ComfyUI and the model weights were not installed. Read-Only is not on the box.
- **Wrote:**
  - `scripts/setup_env.sh`: installs and checks every stage's tools, then writes `log/environment.txt`. It is idempotent; `--no-models` and `--check-only` are options.
  - `config/models.tsv`: ComfyUI weights, pinned to Hugging Face revisions.
  - `pyproject.toml`: Python 3.12, torch 2.8 cu128, WhisperX 3.8.6.
  - `package.json`: puppeteer 24.43.1.
  - `.gitignore`, `CLAUDE.md`, and `log/decisions.md` (Read-Only substitute, model choices).
  - `scripts/hooks/pre-commit` (rejects staged files over 50 MiB) and `scripts/manifest.sh`, both from Ghost in the Machine.
- **Model research (2026-10-19):** the native ComfyUI LTX-2.3 docs (https://docs.comfy.org/tutorials/video/ltx/ltx-2-3) list the files for IA2V (lip sync) and IC-LoRA Union Control (video-to-video). Hugging Face listings gave the FLUX.2 fp8 split files (Comfy-Org/flux2-dev). None of the repos is gated.
- **Fix during the first run:** `grep -q` in a pipeline under `set -o pipefail` let ffmpeg die of SIGPIPE, so the libx264 check failed falsely. Changed to `grep … >/dev/null`.
- **Command:** `scripts/setup_env.sh` (running; its checks are logged when it finishes).
- **Why:** The user asked for everything required to be installed and written down as a script that replicates the environment.

## 2026-10-19T12:07:37-04:00 — Inputs: planning chat archived

- **What:** Fetched the shared planning chat with headless Chrome and converted it to markdown. 14 messages, snapshot "Song: Folks Like Us (AI in politics)", taken 2026-10-19T16:06:31Z.
- **Commands:**
  - `node scripts/fetch_share.mjs https://claude.ai/share/7268f962-e815-4237-b079-564cd6fd8ebd <scratch>/chat`
  - `python3 -I scripts/chat_snapshot_to_md.py docs/planning_chat/planning_chat.json <url> > docs/planning_chat/planning_chat.md`
- **Outputs:** `docs/planning_chat/planning_chat.json` (raw), `docs/planning_chat/planning_chat.md`. Both scripts were copied from Ghost in the Machine unchanged.
- **Why:** The brief lists exports of the planning chats as an input.

## 2026-10-19T12:07:57-04:00 — Inputs: Suno track, stems and generation record

- **What:** Copied the Suno one-shot and stems into the repo, and extracted the clip record from the share page.
  - The share link redirects to `suno.com/song/5dbb89c9-7a04-4a80-8798-a06dba4a37f1`.
  - The clip object (model, style prompt, sliders, and lyrics via the page's React flight row `bc`) is embedded in the server-rendered HTML. WebFetch had only returned a summary.
- **Commands:**
  - `cp ~/Downloads/"Folks Like Us.wav" ~/Downloads/"Folks Like Us Stems.zip" audio/track/`
  - `unzip -n audio/track/"Folks Like Us Stems.zip" -d audio/stems`
  - `node scripts/fetch_suno.mjs https://suno.com/s/WBFA5UlgX7HMQVUm <scratch>/suno`, then the clip object was parsed out of `page.html`
- **Outputs:**
  - `audio/track/Folks Like Us.wav` (48 kHz 16-bit stereo, 141.2 s) and the stems zip;
  - `audio/stems/`: 10 stems (backing vocals, bass, drums, FX, guitar, keyboard, percussion, strings, synth, vocals), each as WAV, MP3 and MIDI;
  - `log/prompts/suno/clip_5dbb89c9.json`, `lyrics_submitted.txt` and `style_prompt_submitted.txt`;
  - `log/human_interventions.md`, entries 1 and 3;
  - `MANIFEST.sha256`.
- **Findings:**
  - The submitted lyrics are the chat's v2 verbatim, stage directions included.
  - The submitted style prompt is a longer rewrite of the chat's v2 prompt.
  - The only slider is `aug_creativity: 1`.
- **Why:** Brief, inputs: the Suno WAV with its take ID, prompt and settings. Human interventions entry 1 is the Suno one-shot.

## 2026-10-19T12:07:59-04:00 — Inputs: the master, suppression off

- **What:** Copied the human's music-deslop M6f 10k run into the repo. The no-fallback output, which is the model's output everywhere, is the master, as the human chose. The with-fallback output is kept for comparison. The mastering report and the per-song fallback regions went into `docs/mastering/`.
- **Commands:**
  - `cp ~/Downloads/music-deslop-m6f-10k-2026-10-18/no-fallback/folks-like-us.wav audio/master/folks_like_us_master_nofallback.wav`
  - `cp …/with-fallback/folks-like-us.wav audio/master/with-fallback/folks_like_us_master_withfallback.wav`
  - `cp …/REPORT.md …/fallback.json docs/mastering/`
- **Checks:**
  - The model's input (`~/Downloads/e2e-eval/folks-like-us-suno.wav`) is byte-identical to `audio/track/Folks Like Us.wav` (sha256 `305cbc0c…`).
  - Both masters are 24-bit 48 kHz stereo, 141.2 s, and not gain-scaled (REPORT.md).
- **F1–F3 candidates** (`fallback.json`, seconds):

  | Region | Start | End | Deepest fade |
  | --- | --- | --- | --- |
  | F1 | 103.437 | 106.094 | 97% |
  | F2 | 124.894 | 130.757 | 100% |
  | F3 | 133.707 | 141.088 | 100% |

  These match the brief's F1–F3 by position. [H] still confirms them by ear before `failure_map.json` is written. Logged in `log/decisions.md`.
- **Outputs:** `audio/master/`, `docs/mastering/REPORT.md`, `docs/mastering/fallback.json`, `MANIFEST.sha256`; human interventions entry 2.
- **Why:** Brief, "The artifact policy". The mastering model's output and logs are archived because they feed S34.

## 2026-10-19T12:13:22-04:00 — Setup: environment installed and verified

- **What:** `scripts/setup_env.sh` finished. It installed the project venv, Puppeteer and Chrome headless shell, ComfyUI v0.42.1 with its venv and three custom nodes, and all 12 weight files in `config/models.tsv` (~85 GB, in `~/ComfyUI/models/_hf/`, linked into place). Every check passes. The versions are in `log/environment.txt`.
- **Fixes during the run:**
  - The Blender GPU check called `gpu.platform` before the gpu module was initialised, which fails in background mode even on a working GPU. It now renders a 64 px Eevee frame first. Result: `NVIDIA GeForce RTX 5090/PCIe/SSE2`, OpenGL backend.
  - The ComfyUI torch install was unpinned. It is now pinned to what was installed and checked: torch 2.14.1, torchvision 0.29.1 and torchaudio 2.11.0, all cu130.
  - `uv venv` for ComfyUI now runs from `~/ComfyUI`, so it no longer warns about this repo's `requires-python`.
- **ComfyUI smoke test:** `~/ComfyUI/.venv/bin/python main.py --listen 127.0.0.1 --port 8189`, then `GET /object_info` returned 1348 nodes (86 LTX) and no import errors. Every model appears in its loader: both LTX-2.3 checkpoints, the FLUX.2 UNet, the Gemma and Mistral text encoders (CLIPLoader types `ltxv` and `flux2`), and the three LoRAs.
- **Commands:** `scripts/setup_env.sh`, then `scripts/setup_env.sh --check-only` after the fixes.
- **Not yet measured:** VRAM and RAM headroom for FLUX.2 and LTX-2.3 on this box (38 GB RAM, 4 GB swap). Time one generation of each before batching (brief, "VRAM plan").
- **Outputs:** `log/environment.txt`.

## 2026-10-19T12:16:14-04:00 — Setup: swap enlarged to 32 GB

- **What:** Resized `/swap.img` from 4 GB to 32 GB, as the human asked (human interventions 4). The existing `/etc/fstab` entry keeps it across reboots. Added an `ensure_swap` step (`SWAP_GB=32`) and a swap check to `scripts/setup_env.sh`, so the environment replicates. The check allows 5% for the swap header.
- **Commands:** `sudo swapoff /swap.img && sudo fallocate -l 32G /swap.img && sudo chmod 600 /swap.img && sudo mkswap /swap.img && sudo swapon /swap.img`; then `scripts/setup_env.sh --check-only` (all ok, "swap 31 GiB").
- **Result:** `swapon --show` reports /swap.img at 32G. RAM plus swap is now about 70 GB.
- **Outputs:** `scripts/setup_env.sh`, `log/environment.txt`.

## 2026-10-19T12:21:01-04:00 — Pre-production 1: as-sung lyrics and timing map

- **What:** Transcribed the vocals stem with WhisperX to find what Suno sang. Wrote the as-sung lyrics. Force-aligned them to the vocals stem with WhisperX and corrected the aligner where sung audio misleads it. Tracked beats on the drums and percussion stems.
- **Model and tool versions:**
  - WhisperX 3.8.6 with faster-whisper `large-v3` (float16, beam 5, no conditioning on previous text, CUDA) for the transcript;
  - WhisperX's English wav2vec2 aligner (`WAV2VEC2_ASR_BASE_960H`, torchaudio) for the alignment;
  - librosa for beats.
- **Commands:** `.venv/bin/python scripts/transcribe_vocals.py`, then `.venv/bin/python scripts/timing_map.py`
- **What Suno sang, compared with `log/prompts/suno/lyrics_submitted.txt`** (from the transcript and the vocals and backing-vocals stem levels):
  1. The bracketed stage directions and "(points off-screen to an empty chair)" are not sung.
  2. Chorus 1 sings "It's apple pie!" twice (55.67 s and 58.90 s). The vocals stem is at about −19 dB at both, so this is not a Whisper repeat.
  3. The tag drops "sung by artificial intelligence". The vocals fall below −58 dB between "written by artificial intelligence" (ends 127.50 s) and "this entire message" (129.88 s), and the line doesn't fit there. The generator cut its own "sung by AI" line.
  4. The outro (134.14–141.20 s) is instrumental. This answers the brief's open item "is it sung or instrumental?": instrumental, 7.1 s.
- **Kept as submitted, for [H] to confirm:** Whisper heard these differently or not at all, but the stem has voice where they belong.
  - "And out past" (Whisper: "now past");
  - "Gonna" in chorus 1 (voice at 41.4–42.0 s);
  - "We" in the final chorus (voice at 88.6–88.9 s);
  - "all" in the final chorus's "bet it all on" (Whisper: "bet it on").
- **Alignment correction (`refine()` in `timing_map.py`):**
  - wav2vec2 placed starts well but missed the ends of held notes. Before ST4, "sky—" ended at 103.71 s although the voice holds to 106.38 s. Chorus 1's second "pie!" ran to its window's edge at 64.85 s.
  - After ST1 it started "—day." at 33.41 s, in silence; the voice returns at 34.40 s.
  - Fix: starts in silence move to the next onset, and the end of a word before a pause moves to where the vocals stem drops 10 dB below its voiced median (−32.4 dB) for 100 ms. 61 of 192 words changed; the originals are kept as `start_aligner`/`end_aligner`.
- **Result:** 83.35 bpm (the prompt asked for 84), 176 beats, downbeat phase 0 (4/4 assumed). Sections, with first vocal at 13.34 s:

  | Section | Start (s) | End (s) |
  | --- | --- | --- |
  | Verse 1 | 13.34 | 35.76 |
  | Chorus | 36.65 | 59.72 |
  | Verse 2 | 64.85 | 86.90 |
  | Final chorus | 88.69 | 109.36 |
  | Tag | 112.14 | 134.14 |
  | Outro | 134.14 | 141.20 |

- **Gaps in the vocal at the stops:**

  | Stop | Gap in the vocal |
  | --- | --- |
  | ST1 | 1.06 s |
  | ST2 | 1.19 s |
  | ST3 | 0.12 s |
  | ST4 | 1.33 s |

  ST3 has no stop in the take, and ST4 is not twice as long as the others. `stops.json` (step 3) measures the whole mix, not only the vocal.
- **Outputs:**
  - `timing/whisper_words.json` and `lyrics/as_sung.txt`;
  - `timing/timing_map.json`: words with scores, lines, sections, beats, downbeats, stop cues, F1–F3 candidates and events;
  - `timing/as_sung_lines.srt` and `timing/as_sung_words.srt`, for checking sync in VLC;
  - `timing/spot_check.md`: five cues and four words for [H].
- **Status:** Waiting for [H]'s spot check of five cues by ear (brief, step 1). Lowest aligner scores, all short unstressed words: "and" (38.25 s, 0.00), "and" (90.31 s, 0.00), "a" (71.42 s, 0.06).

## 2026-10-19T12:23:49-04:00 — Brief: Lyrics section replaced with the as-sung lyrics

- **What:** As the brief's step 1 asks, replaced the Lyrics section of the brief (Claude Doc `S37uBB1UQJGfxSWx7wQ6Ek`; doc rev 9 → 10) with `lyrics/as_sung.txt`. Each section is marked with its times, ST1–ST4 and F1–F3 are placed at their measured times, and the intro paragraph lists Suno's three changes and the four words awaiting [H].
- **Tool:** Claude Docs `update`, replacing the 13 lyric blocks, guarded on rev 9.
- **Why:** Brief, pre-production step 1.

## 2026-10-19T12:23:49-04:00 — Pre-production 2: failure map

- **What:** Wrote `timing/failure_map.json` from the mastering model's fallback log. Checked it against the audio by subtracting the with-fallback master from the no-fallback master: inside each region the difference is the model's failing change, and everywhere else it should be silence. Cut A/B listening clips for [H].
- **Command:** `.venv/bin/python scripts/failure_map.py`
- **Result:**

  | Region | Time (s) | Words | Artifact | Relative to the master |
  | --- | --- | --- | --- | --- |
  | F1 | 103.437–106.094 | "with sky—" (the held note) | −74.8 dB | −59.3 dB |
  | F2 | 124.894–130.757 | "written by artificial intelligence, this entire message" | −45.4 dB | −29.7 dB |
  | F3 | 133.707–141.088 | "artificial intelligence." then the instrumental outro | −42.3 dB | −26.7 dB |

  Outside the regions the two masters differ by −193.0 dB, so they are identical there. The log's regions are exactly where the model changed something.
- **Flag for [H]:** F1's change is about 59 dB under the music, which is probably inaudible. The fallback detector fired there (per-bin gain jitter), but the audible "rhymes with sky" distortion may be mostly in Suno's original. Compare `F1_nofallback.wav` and `F1_withfallback.wav`. If F1 isn't audible in the master, the G passes still sit on these boundaries (the brief cuts them to the failure map), but the closing bookend card's claim ("couldn't fix the three places") may need checking.
- **Outputs:** `timing/failure_map.json` (`confirmed_by_ear: null` per region); `timing/failure_clips/F{1,2,3}_{nofallback,withfallback,artifact}.wav` (git-ignored, regenerable; each clip starts at the region's `clip_offset_s`).
- **Status:** Waiting for [H] to confirm every boundary by ear (brief, step 2).

## 2026-10-19T12:23:49-04:00 — Pre-production 3: stop map

- **What:** Measured the master's level through each stop's vocal gap and checked each stem. No stop is silent in the take, so the edits E makes are written to `timing/stops.json` (decision logged). Rendered a preview of the stopped master.
- **Command:** `.venv/bin/python scripts/stop_map.py`
- **Result:** "Real silence" in every gap is 0.00 s at −60 dB. The made silences are 1.03, 1.16, 0.81 and 2.02 s, and the edit runs 142.64 s. In the preview each stop measures −240 dB inside, with the music at −15 to −25 dB within 0.2 s either side.
- **Answers the brief's open item:** "Did the Suno take honor the four stops, or does E have to make them?" E has to make all four.
- **Outputs:** `timing/stops.json`; `audio/master/preview_stops.wav` (git-ignored, regenerable with this command).

## 2026-10-19T12:24:28-04:00 — Pre-production 4: style spec

- **What:** Wrote `style/style_spec.md` from the brief's Look line and step 4. It covers format, light, camera, grade, the town palette, on-screen text, and the prompt fragments every S, V and L generation shares.
  - Format: 24 fps, a 180° shutter, and 1920×1080 working resolution (delivery resolution decided at the final cut).
  - Light: key at 8–12° and about 3200 K. The building's light at about 5600 K takes over as the running gags escalate.
  - Camera: 35/50/85 mm at f/2–2.8, push-ins at 3–8% of frame width per second, and at most one flare per section, made in B.
  - Grade: warm highlights, teal shadows, 3% lifted blacks, halation and grain applied in E, and the building always neutral gray.
- **Why:** Brief, pre-production step 4. No real political ads were downloaded or used as references.
- **Open:** the two campaign fonts (SIL OFL) are chosen when the O templates are built.

## 2026-10-19T12:26:53-04:00 — Timing check video for [H]

- **What:** VLC shows no subtitles over an audio-only file, so the agent rendered a check video: a black 1280×720 frame at 24 fps showing each word in the center at its timing-map start, the whole line at the bottom, and the timecode and frame number top left, over the no-fallback master. The human asked for VLC to be opened, and the agent opened it on this video.
- **Command:** `ffmpeg -f lavfi -i color=c=black:s=1280x720:r=24 -i audio/master/folks_like_us_master_nofallback.wav -shortest -vf "subtitles=timing/as_sung_lines.srt:force_style='Fontsize=20,Alignment=2,MarginV=40',subtitles=timing/as_sung_words.srt:force_style='Fontsize=48,Alignment=10,Bold=1',drawtext=text='%{pts\:hms}':x=40:y=40:fontsize=36:fontcolor=white,drawtext=text='frame %{frame_num}':x=40:y=90:fontsize=24:fontcolor=gray" -c:v libx264 -preset veryfast -crf 23 -c:a aac -b:a 256k renders/check/timing_check.mp4`
- **Fix:** the first render used `Alignment=5`. In libass's legacy SSA numbering that is top-left, so the word sat over the timecode. Changed to 10 (middle center) and checked a frame at 34.5 s.
- **Outputs:** `renders/check/timing_check.mp4` (git-ignored, regenerable with this command); `timing/spot_check.md` now points at it.

## 2026-10-19T12:31:04-04:00 — Pre-production 1 complete: timing map confirmed

- **What:** [H] confirmed the five cues and the four doubtful words (human interventions 5). `lyrics/as_sung.txt` and `timing/timing_map.json` need no change. In the brief's Lyrics intro, the "until [H] confirms" sentence now records the confirmation (doc rev 10 → 11, a text replace).
- **Outputs:** `timing/spot_check.md` (result section).
- **Still open for [H]:** the failure-map boundaries (step 2, `timing/failure_clips/`) and a listen to the made stops (`audio/master/preview_stops.wav`).

## 2026-10-19T12:35:45-04:00 — Pre-production 3 redone: no made stops; shots reflowed

- **What:** As the human directed (human interventions 6), removed the made silences. `scripts/stop_map.py` now only measures each stop's vocal gap and the mix level in it. Reflowed the brief's stop shots (S10, S16, S21, S22, S30) around the real vocal gaps, where the band plays on. Answered and ticked four open items and the first review checkpoint. Details are in `log/decisions.md`.
- **Commands:** `.venv/bin/python scripts/stop_map.py`; Claude Docs `update` (doc rev 11 → 26, text replaces and `checked` attributes); `mv audio/master/preview_stops.wav audio/master/preview_stops_rejected.wav`.
- **Result:** `timing/stops.json` holds the vocal gaps (1.06, 1.19, 0.12 and 1.33 s), the mix level in each (−12 to −37 dB), and 0.00 s of real silence everywhere, with no edits. `style/style_spec.md` now uses edit time = source time.
- **Outputs:** `timing/stops.json`, `scripts/stop_map.py`, `style/style_spec.md`, `log/decisions.md`.

## 2026-10-19T12:35:45-04:00 — Pre-production 2 complete: failure map confirmed

- **What:** [H] confirmed F1–F3 by ear (human interventions 7). Recorded this in `scripts/failure_map.py` (`CONFIRMED`) and regenerated `timing/failure_map.json`; every region's `confirmed_by_ear` is filled in. The brief's open item on the deslop log is answered (previous entry).
- **Command:** `.venv/bin/python scripts/failure_map.py`
- **Note:** F1 is audible to [H] although the model's change there measures 59 dB under the music, so the closing bookend's claim ("couldn't fix the three places") stands.
- **Pre-production status:** steps 1–4 are done. Next are step 5 (Blender set kit) and step 6 (reference stills).

## 2026-10-19T12:37:14-04:00 — Brief: cold open without the F1 glitch

- **What:** Updated S01 in the brief: the hook keeps the caption swap but not the F1 glitch, has no G pass, and takes its audio from the with-fallback master. Ticked the last open item, "Save it (S01)." Doc rev 26 → 28, as text replaces and a `checked` attribute.
- **Why:** Human interventions 8; decision logged.
- **Pre-production status:** steps 1–4 are done and every open item is answered. Next are step 5 (Blender set kit) and step 6 (reference stills).

## 2026-10-19T12:57:28-04:00 — Pre-production 5 [B]: set kit and contact sheet

- **What:** Built the town in Blender from code, defined every B shot's fixed camera, continuity and cast, rendered a still of each with all guide passes, and laid out the contact sheet for the [H] checkpoint.
- **Scripts and config:**
  - `scripts/blender/build_town.py` writes `scenes/town.blend` (git-ignored, regenerable): farmhouse and porch (master set), kitchen, yard, ray-aligned cornfield with a farm track, pasture and cows, water tower with gauge, power lines to the campus, main street (diner with TV wall and street window, church marquee, yard signs), the FUTURE SITE OF sign with bunting, B1's cranes, and the campus. Characters are mannequin stand-ins (singer in five poses, Grandma, the kid in two, the dog, patrons). Every text surface is a blank `txt_*` plane.
  - `config/continuity.json`: the running-gags table as parameters per section (stage, cranes, floodlights, LED, the building's light on the farm, sun, sky, practicals, gauge), animatable per shot.
  - `config/shot_cues.json` and `scripts/shot_times.py` → `timing/shot_times.json`: every song shot S04–S33 resolved from its lyric cue to time and frame (24 fps). The new `mid:` cue handles held notes.
  - `config/shots_b.json`: 25 B shots (S04, S05, S08, S09, S11, S12, S14, S17–S20, S22, S26, S27a–e, S28a–b, S29, S31, S33, and the vertical S29v and S31v), each with camera, lens, f-stop, move (push, dolly or pan, eased), focus, cast, depth range and overrides.
  - `scripts/blender/render_shot.py` writes per frame: beauty (AgX), depth (16-bit relative inverse depth), camera-space normals, building mask, a multilayer EXR, `shot.json`, and `anchors.json` (each text surface's corners per frame, with an occlusion flag).
  - `scripts/contact_sheet.py` → `renders/b/contact_sheet.png`.
- **Commands:**
  - `blender -b --factory-startup --python scripts/blender/build_town.py`
  - `.venv/bin/python scripts/shot_times.py`
  - `blender -b scenes/town.blend --python scripts/blender/render_shot.py -- all --still --res 960x540 --samples 32 --out renders/b/contact` (about 15 s for all 25)
  - `.venv/bin/python scripts/contact_sheet.py`
- **Fixes found by looking at the renders:**
  - Blender 5.2 needs `media_type = "MULTI_LAYER_IMAGE"` before a multilayer EXR.
  - OIIO's `read_image` must be given the subimage, or every pass reads as Combined.
  - Single-channel PNGs need an explicit channel axis.
  - Depth changed from linear mist to relative inverse depth: linear washed the porch out white.
  - Clearing animation keeps the last keyed values, so a stand-in moved in one shot (S19's singer in the kitchen) stayed there for S22. Built transforms are now restored per shot.
  - Cast props now bring their text surfaces.
  - A storefront overlapped the diner and blocked its window. The plot across the street is now a parking lot.
  - The marquee faced away from the street. A storefront sat on the church lot.
  - The porch post stood in front of the singer.
  - The campus concrete was too close to the sky's colour.
- **Not built yet, for the V stage:** OpenPose-style skeletons of the stand-ins (pose guidance alongside depth), full-length plates at 1920×1080, and the pie tin's reflection.
- **Status:** waiting for [H] to review the contact sheet (brief, review checkpoint "Blender contact sheet").

## 2026-10-19T13:01:01-04:00 — Pre-production 5 approved

- **What:** [H] approved the contact sheet (human interventions 9). The brief's review checkpoint is ticked (doc rev 28 → 29).

## 2026-10-19T13:02:38-04:00 — Set kit: B plates added for the V-only shots S06, S13, S15, S16

- **What:** The first set kit gave cameras only to shots whose pipe lists B. The brief defines V as "shots generated over Blender renders", so the V-only shots need plates too. Added:
  - **S06:** low on the porch; the dog faces the building past the house corner, and the singer stands above it.
  - **S13:** the kid in the pasture, with the kite string rising toward the power lines and water tower.
  - **S15:** a low angle on the porch; the singer's two fingers against the sky.
  - **S16:** open sky over the farm, for the plane and the smoke pie.
- **Why:** The human asked about the missing dog shot. The dog was in S05, and the human said to carry on, but the check showed S06 had no plate.
- **Command:** `blender -b scenes/town.blend --python scripts/blender/render_shot.py -- S06 S13 S15 S16 --still --res 960x540 --samples 32 --out renders/b/contact`; `.venv/bin/python scripts/contact_sheet.py` (29 shots).
- **Fix:** S13's first aim (target z 12) left the kid below frame; it is now (74, −3, 6.5).
- **Note:** these four plates came after [H]'s approval of the sheet; they are in the updated `renders/b/contact_sheet.png`.

## 2026-10-19T13:03:34-04:00 — S: reference stills (singer)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, text encoder `mistral_3_small_flux2_fp4_mixed.safetensors`, VAE `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0; ComfyUI (`scripts/stills.py`, graph as the `image_flux2_fp8` template, text-to-image).
- **Prompts:** `log/prompts/stills/<item>.txt`. **Inputs:** none (text only).
- **Command:** `.venv/bin/python scripts/stills.py singer --seeds 1001`

| Item | Seed | Output | Seconds | Status |
| --- | --- | --- | --- | --- |
| singer | 1001 | `takes/stills/singer/singer_s1001.png` | 77.0 | pending [H] |

## 2026-10-19T13:04:59-04:00 — S: reference stills (singer, grandma, kid, dog, granddad_photo, pie, mug_blank)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, text encoder `mistral_3_small_flux2_fp4_mixed.safetensors`, VAE `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0; ComfyUI (`scripts/stills.py`, graph as the `image_flux2_fp8` template, text-to-image).
- **Prompts:** `log/prompts/stills/<item>.txt`. **Inputs:** none (text only).
- **Command:** `.venv/bin/python scripts/stills.py `

| Item | Seed | Output | Seconds | Status |
| --- | --- | --- | --- | --- |
| singer | 1002 | `takes/stills/singer/singer_s1002.png` | 52.4 | pending [H] |
| singer | 1003 | `takes/stills/singer/singer_s1003.png` | 51.1 | pending [H] |
| singer | 1004 | `takes/stills/singer/singer_s1004.png` | 50.1 | pending [H] |
| grandma | 1001 | `takes/stills/grandma/grandma_s1001.png` | 52.1 | pending [H] |
| grandma | 1002 | `takes/stills/grandma/grandma_s1002.png` | 50.1 | pending [H] |
| grandma | 1003 | `takes/stills/grandma/grandma_s1003.png` | 50.1 | pending [H] |
| grandma | 1004 | `takes/stills/grandma/grandma_s1004.png` | 50.1 | pending [H] |
| kid | 1001 | `takes/stills/kid/kid_s1001.png` | 51.1 | pending [H] |
| kid | 1002 | `takes/stills/kid/kid_s1002.png` | 50.1 | pending [H] |
| kid | 1003 | `takes/stills/kid/kid_s1003.png` | 50.1 | pending [H] |
| kid | 1004 | `takes/stills/kid/kid_s1004.png` | 50.1 | pending [H] |
| dog | 1001 | `takes/stills/dog/dog_s1001.png` | 51.1 | pending [H] |
| dog | 1002 | `takes/stills/dog/dog_s1002.png` | 50.0 | pending [H] |
| dog | 1003 | `takes/stills/dog/dog_s1003.png` | 50.1 | pending [H] |
| dog | 1004 | `takes/stills/dog/dog_s1004.png` | 50.1 | pending [H] |
| granddad_photo | 1001 | `takes/stills/granddad_photo/granddad_photo_s1001.png` | 51.1 | pending [H] |
| granddad_photo | 1002 | `takes/stills/granddad_photo/granddad_photo_s1002.png` | 50.1 | pending [H] |
| granddad_photo | 1003 | `takes/stills/granddad_photo/granddad_photo_s1003.png` | 50.1 | pending [H] |
| granddad_photo | 1004 | `takes/stills/granddad_photo/granddad_photo_s1004.png` | 50.1 | pending [H] |
| pie | 1001 | `takes/stills/pie/pie_s1001.png` | 51.1 | pending [H] |
| pie | 1002 | `takes/stills/pie/pie_s1002.png` | 50.1 | pending [H] |
| pie | 1003 | `takes/stills/pie/pie_s1003.png` | 50.1 | pending [H] |
| pie | 1004 | `takes/stills/pie/pie_s1004.png` | 50.1 | pending [H] |
| mug_blank | 1001 | `takes/stills/mug_blank/mug_blank_s1001.png` | 51.1 | pending [H] |
| mug_blank | 1002 | `takes/stills/mug_blank/mug_blank_s1002.png` | 50.1 | pending [H] |
| mug_blank | 1003 | `takes/stills/mug_blank/mug_blank_s1003.png` | 50.1 | pending [H] |
| mug_blank | 1004 | `takes/stills/mug_blank/mug_blank_s1004.png` | 50.1 | pending [H] |

## 2026-10-19T13:28:20-04:00 — S: reference stills (granddad_photo)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, text encoder `mistral_3_small_flux2_fp4_mixed.safetensors`, VAE `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0; ComfyUI (`scripts/stills.py`, graph as the `image_flux2_fp8` template, text-to-image).
- **Prompts:** `log/prompts/stills/<item>.txt`. **Inputs:** none (text only).
- **Command:** `.venv/bin/python scripts/stills.py granddad_photo`

| Item | Seed | Output | Seconds | Status |
| --- | --- | --- | --- | --- |
| granddad_photo_v2 | 1005 | `takes/stills/granddad_photo/granddad_photo_v2_s1005.png` | 51.1 | pending [H] |
| granddad_photo_v2 | 1006 | `takes/stills/granddad_photo/granddad_photo_v2_s1006.png` | 50.2 | pending [H] |
| granddad_photo_v2 | 1007 | `takes/stills/granddad_photo/granddad_photo_v2_s1007.png` | 50.3 | pending [H] |
| granddad_photo_v2 | 1008 | `takes/stills/granddad_photo/granddad_photo_v2_s1008.png` | 50.2 | pending [H] |

**Review (agent, before [H]):** 32 candidates. The v1 Granddad photo (seeds 1001–1004) is rejected by the agent: all four buildings have rows of windows, and the brief's building is windowless. The prompt was revised to "a huge featureless gray concrete box … no windows, no openings and no markings" (`log/prompts/stills/granddad_photo_v2.txt`) and rerun with seeds 1005–1008; all four came out windowless. Review grids: `takes/stills/review_<item>.png`. Every candidate waits for [H] to pick one per item (brief: "[H] approves each sheet").

## 2026-10-19T13:41:37-04:00 — Pre-production 6 complete: reference stills approved

- **[H]** took the agent's pick for every item ("all yours, go ahead"; human interventions 10).
- **Kept**, one per item; copies are at stable paths for later stages (`config/stills.json` → `kept`):

  | Item | Kept take | Copy |
  | --- | --- | --- |
  | singer | `takes/stills/singer/singer_s1002.png` | `takes/stills/kept/singer.png` |
  | grandma | `takes/stills/grandma/grandma_s1001.png` | `takes/stills/kept/grandma.png` |
  | kid | `takes/stills/kid/kid_s1002.png` | `takes/stills/kept/kid.png` |
  | dog | `takes/stills/dog/dog_s1003.png` | `takes/stills/kept/dog.png` |
  | granddad_photo | `takes/stills/granddad_photo/granddad_photo_v2_s1007.png` | `takes/stills/kept/granddad_photo.png` |
  | pie | `takes/stills/pie/pie_s1003.png` | `takes/stills/kept/pie.png` |
  | mug_blank | `takes/stills/mug_blank/mug_blank_s1003.png` | `takes/stills/kept/mug_blank.png` |

- **Rejected:** the other 25 candidates, including all four v1 Granddad photos (buildings with windows). They stay in `takes/stills/` and are not used.
- **Brief:** the review checkpoint "[H] Character sheets and prop stills approved" is ticked.

## 2026-10-19T13:48:14-04:00 — Pre-production 7: VRAM plan, with V and L measured

- **What:** Measured one job of each heavy stage on this box and wrote `style/vram_plan.md`: the order (S, V, L, then G and O), freeing memory between stages, no parallel GPU or RAM users, clip lengths, and the compute budget.
- **Tools:**
  - `scripts/comfy_ui_to_api.mjs` converts a ComfyUI editor-format workflow to API format, using the frontend's own `graphToPrompt()` in headless Chrome. Applied to the LTX-2.3 templates `video_ltx2_3_ic_lora` (V) and `video_ltx2_3_ia2v` (L), copied to `comfy/templates/` and converted to `comfy/api/`.
  - `scripts/ltx_v.py` runs V from a depth video and a first frame, sampling GPU, RAM and swap once a second.
- **Test inputs:** S05 rendered at 1280×704 for frames 320–416 (97 frames, 58 s), with `blender -b scenes/town.blend --python scripts/blender/render_shot.py -- S05 --frames 320:417 --res 1280x704 --samples 32 --out renders/b/test_v`. The depth and beauty passes were encoded to mp4. The singer's close-up was cropped from `takes/stills/kept/singer.png`, and the vocal is 13.0–17.0 s of the master.
- **Results:**

  | Test | Seed | Time | GPU peak | RAM peak | Swap peak | Output |
  | --- | --- | --- | --- | --- | --- | --- |
  | V, Blender depth as the guide | 1 | 43 s | 32.1 GB | 37.0 GB | 5.3 GB | the gray depth image reproduced (rejected; test) |
  | V, template MoGe path on the Blender beauty video | 1 | 44 s | — | — | — | the blocky first frame kept (rejected; test) |
  | L, singer close-up + 4 s of vocal | template's | 43 s | 31.9 GB | 36.6 GB | 7.1 GB | photoreal singing take, identity kept, mouth cropped (test) |

- **Findings for V:** the first frame must be a photoreal FLUX.2 keyframe, and the Blender depth needs MoGe's control convention, or MoGe run on the plate. Both are in the plan.
- **Pre-production status:** steps 1–7 are done. Every pre-production [H] checkpoint is ticked except those that belong to later stages.

## 2026-10-19T13:52:52-04:00 — S: keyframes (S05, S12, S20)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0; reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S05 S12 S20`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S05 | 2001 | renders/b/keyframe/S05/beauty/00320.png, takes/stills/kept/singer.png, takes/stills/kept/dog.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S05/S05_s2001.png` | 221.9 | superseded (later pick, see keyframe_picks.json) |
| S05 | 2002 | renders/b/keyframe/S05/beauty/00320.png, takes/stills/kept/singer.png, takes/stills/kept/dog.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S05/S05_s2002.png` | 207.2 | superseded (later pick, see keyframe_picks.json) |
| S12 | 2001 | renders/b/keyframe/S12/beauty/00880.png, takes/stills/kept/singer.png | `takes/keyframes/S12/S12_s2001.png` | 115.4 | pending [H] |
| S12 | 2002 | renders/b/keyframe/S12/beauty/00880.png, takes/stills/kept/singer.png | `takes/keyframes/S12/S12_s2002.png` | 114.2 | pending [H] |
| S20 | 2001 | renders/b/keyframe/S20/beauty/01829.png | `takes/keyframes/S20/S20_s2001.png` | 82.3 | pending [H] |
| S20 | 2002 | renders/b/keyframe/S20/beauty/01829.png | `takes/keyframes/S20/S20_s2002.png` | 82.1 | pending [H] |

**Pilot review (agent, 2026-10-19T14:08:13-04:00):** S05, S12 and S20, two seeds each, took 82–222 s per keyframe; time grows with the number of references.
- **Layout:** the layout's depth edges line up with the generated porch, corn rows and track. People drift a little from the stand-ins' positions, which the V stage will need to handle.
- **Problems, and the fixes in the revised prompts:**
  - S12's building got windows and came out too big for B2. S12 v2 and the shared style now specify "featureless windowless concrete box … exactly as large and as far away as in the layout".
  - S20 seed 2001 put a dog in the diner. S20 v2 adds "No animals indoors".
  - "Teal shadows" turned S05's white posts teal; the style now says "neutral shadows". S05 v1 stays as it is, for [H] to judge.
- **Batch:** all 29 V shots: S05 v1 kept, S12 and S20 at v2, and 26 new prompts with each shot's cast as references and final-chorus lighting from the building. Command: `.venv/bin/python scripts/keyframes.py`.

## 2026-10-19T14:08:00-04:00 — S: keyframes (S04, S05, S06, S08, S09, S11, S12, S13, S14, S15, S16, S17, S18, S19, S20, S22, S26, S27a, S27b, S27c, S27d, S27e, S28a, S28b, S29, S31, S33, S29v, S31v)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0; reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py `

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S04 | 2001 | renders/b/keyframe/S04/beauty/00000.png | `takes/keyframes/S04/S04_s2001.png` | 81.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S04 | 2002 | renders/b/keyframe/S04/beauty/00000.png | `takes/keyframes/S04/S04_s2002.png` | 82.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S06 | 2001 | renders/b/keyframe/S06/beauty/00420.png, takes/stills/kept/dog.png, takes/stills/kept/singer.png | `takes/keyframes/S06/S06_s2001.png` | 159.2 | superseded (later pick, see keyframe_picks.json) |
| S06 | 2002 | renders/b/keyframe/S06/beauty/00420.png, takes/stills/kept/dog.png, takes/stills/kept/singer.png | `takes/keyframes/S06/S06_s2002.png` | 158.2 | superseded (later pick, see keyframe_picks.json) |
| S08 | 2001 | renders/b/keyframe/S08/beauty/00509.png | `takes/keyframes/S08/S08_s2001.png` | 83.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S08 | 2002 | renders/b/keyframe/S08/beauty/00509.png | `takes/keyframes/S08/S08_s2002.png` | 82.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S09 | 2001 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_s2001.png` | 83.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S09 | 2002 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_s2002.png` | 82.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S11 | 2001 | renders/b/keyframe/S11/beauty/00826.png | `takes/keyframes/S11/S11_s2001.png` | 83.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S11 | 2002 | renders/b/keyframe/S11/beauty/00826.png | `takes/keyframes/S11/S11_s2002.png` | 82.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S12_v2 | 2001 | renders/b/keyframe/S12/beauty/00880.png, takes/stills/kept/singer.png | `takes/keyframes/S12/S12_v2_s2001.png` | 115.2 | superseded (later pick, see keyframe_picks.json) |
| S12_v2 | 2002 | renders/b/keyframe/S12/beauty/00880.png, takes/stills/kept/singer.png | `takes/keyframes/S12/S12_v2_s2002.png` | 114.3 | superseded (later pick, see keyframe_picks.json) |
| S13 | 2001 | renders/b/keyframe/S13/beauty/00980.png, takes/stills/kept/kid.png | `takes/keyframes/S13/S13_s2001.png` | 115.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S13 | 2002 | renders/b/keyframe/S13/beauty/00980.png, takes/stills/kept/kid.png | `takes/keyframes/S13/S13_s2002.png` | 114.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S14 | 2001 | renders/b/keyframe/S14/beauty/00993.png | `takes/keyframes/S14/S14_s2001.png` | 83.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S14 | 2002 | renders/b/keyframe/S14/beauty/00993.png | `takes/keyframes/S14/S14_s2002.png` | 82.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S15 | 2001 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_s2001.png` | 115.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S15 | 2002 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_s2002.png` | 114.3 | rejected (agent review: building, framing drift, extras or text; see note) |
| S16 | 2001 | renders/b/keyframe/S16/beauty/01308.png | `takes/keyframes/S16/S16_s2001.png` | 82.3 | rejected (agent review: building, framing drift, extras or text; see note) |
| S16 | 2002 | renders/b/keyframe/S16/beauty/01308.png | `takes/keyframes/S16/S16_s2002.png` | 82.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S17 | 2001 | renders/b/keyframe/S17/beauty/01336.png, takes/stills/kept/grandma.png, takes/stills/kept/pie.png | `takes/keyframes/S17/S17_s2001.png` | 159.3 | rejected (agent review: building, framing drift, extras or text; see note) |
| S17 | 2002 | renders/b/keyframe/S17/beauty/01336.png, takes/stills/kept/grandma.png, takes/stills/kept/pie.png | `takes/keyframes/S17/S17_s2002.png` | 158.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S18 | 2001 | renders/b/keyframe/S18/beauty/01556.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S18/S18_s2001.png` | 115.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S18 | 2002 | renders/b/keyframe/S18/beauty/01556.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S18/S18_s2002.png` | 114.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S19 | 2001 | renders/b/keyframe/S19/beauty/01751.png, takes/stills/kept/singer.png | `takes/keyframes/S19/S19_s2001.png` | 115.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S19 | 2002 | renders/b/keyframe/S19/beauty/01751.png, takes/stills/kept/singer.png | `takes/keyframes/S19/S19_s2002.png` | 114.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S20_v2 | 2001 | renders/b/keyframe/S20/beauty/01829.png | `takes/keyframes/S20/S20_v2_s2001.png` | 83.1 | kept ([H] approved 2026-10-20) |
| S20_v2 | 2002 | renders/b/keyframe/S20/beauty/01829.png | `takes/keyframes/S20/S20_v2_s2002.png` | 82.1 | superseded (later pick, see keyframe_picks.json) |
| S22 | 2001 | renders/b/keyframe/S22/beauty/02050.png, takes/stills/kept/singer.png | `takes/keyframes/S22/S22_s2001.png` | 115.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S22 | 2002 | renders/b/keyframe/S22/beauty/02050.png, takes/stills/kept/singer.png | `takes/keyframes/S22/S22_s2002.png` | 114.3 | rejected (agent review: building, framing drift, extras or text; see note) |
| S26 | 2001 | renders/b/keyframe/S26/beauty/02242.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S26/S26_s2001.png` | 159.4 | superseded (later pick, see keyframe_picks.json) |
| S26 | 2002 | renders/b/keyframe/S26/beauty/02242.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S26/S26_s2002.png` | 158.2 | superseded (later pick, see keyframe_picks.json) |
| S27a | 2001 | renders/b/keyframe/S27a/beauty/02320.png, takes/stills/kept/grandma.png | `takes/keyframes/S27a/S27a_s2001.png` | 115.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S27a | 2002 | renders/b/keyframe/S27a/beauty/02320.png, takes/stills/kept/grandma.png | `takes/keyframes/S27a/S27a_s2002.png` | 114.4 | rejected (agent review: building, framing drift, extras or text; see note) |
| S27b | 2001 | renders/b/keyframe/S27b/beauty/02331.png, takes/stills/kept/kid.png | `takes/keyframes/S27b/S27b_s2001.png` | 115.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S27b | 2002 | renders/b/keyframe/S27b/beauty/02331.png, takes/stills/kept/kid.png | `takes/keyframes/S27b/S27b_s2002.png` | 114.3 | rejected (agent review: building, framing drift, extras or text; see note) |
| S27c | 2001 | renders/b/keyframe/S27c/beauty/02341.png | `takes/keyframes/S27c/S27c_s2001.png` | 83.1 | kept ([H] approved 2026-10-20) |
| S27c | 2002 | renders/b/keyframe/S27c/beauty/02341.png | `takes/keyframes/S27c/S27c_s2002.png` | 82.1 | superseded (later pick, see keyframe_picks.json) |
| S27d | 2001 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_s2001.png` | 83.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S27d | 2002 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_s2002.png` | 82.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S27e | 2001 | renders/b/keyframe/S27e/beauty/02362.png | `takes/keyframes/S27e/S27e_s2001.png` | 83.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S27e | 2002 | renders/b/keyframe/S27e/beauty/02362.png | `takes/keyframes/S27e/S27e_s2002.png` | 82.3 | rejected (agent review: building, framing drift, extras or text; see note) |
| S28a | 2001 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_s2001.png` | 83.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S28a | 2002 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_s2002.png` | 82.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S28b | 2001 | renders/b/keyframe/S28b/beauty/02382.png | `takes/keyframes/S28b/S28b_s2001.png` | 83.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S28b | 2002 | renders/b/keyframe/S28b/beauty/02382.png | `takes/keyframes/S28b/S28b_s2002.png` | 82.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S29 | 2001 | renders/b/keyframe/S29/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29/S29_s2001.png` | 115.1 | superseded (later pick, see keyframe_picks.json) |
| S29 | 2002 | renders/b/keyframe/S29/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29/S29_s2002.png` | 114.3 | superseded (later pick, see keyframe_picks.json) |
| S31 | 2001 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_s2001.png` | 159.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S31 | 2002 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_s2002.png` | 158.3 | rejected (agent review: building, framing drift, extras or text; see note) |
| S33 | 2001 | renders/b/keyframe/S33/beauty/03219.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S33/S33_s2001.png` | 159.3 | superseded (later pick, see keyframe_picks.json) |
| S33 | 2002 | renders/b/keyframe/S33/beauty/03219.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S33/S33_s2002.png` | 158.2 | superseded (later pick, see keyframe_picks.json) |
| S29v | 2001 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_s2001.png` | 115.1 | rejected (agent review: building, framing drift, extras or text; see note) |
| S29v | 2002 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_s2002.png` | 114.3 | rejected (agent review: building, framing drift, extras or text; see note) |
| S31v | 2001 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_s2001.png` | 159.2 | rejected (agent review: building, framing drift, extras or text; see note) |
| S31v | 2002 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_s2002.png` | 158.2 | rejected (agent review: building, framing drift, extras or text; see note) |

## 2026-10-19T17:29:37-04:00 — S: keyframes (S18, S09, S15)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise 0.85 from the layout (v3 and later); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S18 S09 S15 --seeds 2001 --denoise 0.85`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S18_v3_d85 | 2001 | renders/b/keyframe/S18/beauty/01556.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S18/S18_v3_d85_s2001.png` | 96.3 | rejected (test: denoise sweep for v3) |
| S09_v3_d85 | 2001 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_v3_d85_s2001.png` | 71.1 | rejected (test: denoise sweep for v3) |
| S15_v3_d85 | 2001 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_v3_d85_s2001.png` | 99.1 | rejected (test: denoise sweep for v3) |

## 2026-10-19T17:34:04-04:00 — S: keyframes (S18, S09, S15)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise 0.7 from the layout (v3 and later); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S18 S09 S15 --seeds 2001 --denoise 0.7`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S18_v3_d70 | 2001 | renders/b/keyframe/S18/beauty/01556.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S18/S18_v3_d70_s2001.png` | 82.3 | rejected (test: denoise sweep for v3) |
| S09_v3_d70 | 2001 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_v3_d70_s2001.png` | 59.3 | rejected (test: denoise sweep for v3) |
| S15_v3_d70 | 2001 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_v3_d70_s2001.png` | 83.1 | rejected (test: denoise sweep for v3) |

## 2026-10-19T17:38:06-04:00 — S: keyframes (S15, S18, S09)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise 0.95 from the layout (v3 and later); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S15 S18 S09 --seeds 2001 --denoise 0.95`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S15_v3_d95 | 2001 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_v3_d95_s2001.png` | 110.1 | rejected (test: denoise sweep for v3) |
| S18_v3_d95 | 2001 | renders/b/keyframe/S18/beauty/01556.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S18/S18_v3_d95_s2001.png` | 111.1 | rejected (test: denoise sweep for v3) |
| S09_v3_d95 | 2001 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_v3_d95_s2001.png` | 80.1 | rejected (test: denoise sweep for v3) |

## 2026-10-19T17:43:08-04:00 — S: keyframes (S15, S18, S09)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise 0.92 from the layout (v3 and later); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S15 S18 S09 --seeds 2001 --denoise 0.92`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S15_v3_d92 | 2001 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_v3_d92_s2001.png` | 107.3 | rejected (test: denoise sweep for v3) |
| S18_v3_d92 | 2001 | renders/b/keyframe/S18/beauty/01556.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S18/S18_v3_d92_s2001.png` | 107.1 | rejected (test: denoise sweep for v3) |
| S09_v3_d92 | 2001 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_v3_d92_s2001.png` | 77.5 | rejected (test: denoise sweep for v3) |

## 2026-10-19T17:48:36-04:00 — S: keyframes (S18, S09, S15)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise 0.92 from the layout (v3 and later); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S18 S09 S15 --seeds 2001`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S18_v4 | 2001 | renders/b/keyframe/S18/beauty/01556.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S18/S18_v4_s2001.png` | 107.1 | kept ([H] approved 2026-10-20) |
| S09_v4 | 2001 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_v4_s2001.png` | 77.1 | pending [H] |
| S15_v4 | 2001 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_v4_s2001.png` | 107.4 | pending [H] |

### Note — agent review of the first keyframe batch (2026-10-19)

The first batch (v1/v2, pure reference editing) mostly failed: (1) the shared style sentence about the building put a large concrete box into verse-1 shots where the layout has none (S09, S13, S14, S16–S19); (2) with the layout only a reference, the camera drifted, worst on close-ups (S18, S28b, S15); (3) "campaign commercial" wording added crowds, extra dogs and a camera crew, and the bill and gauge got printing. Kept as candidates for [H]: S05, S06, S12_v2, S20_v2, S26, S27c, S29, S33. Fix (v3/v4, `scripts/keyframes.py`): start from the VAE-encoded layout at denoise 0.92 (0.70 and 0.85 kept the Blender look; 0.95 lost close-up framing), building sentence chosen from the layout's building_mask coverage, positive-only wording plus an "empty scene" sentence (negations added the crowds). Tested on S09, S15, S18; the 21 failed shots re-run at v4.

## 2026-10-19T17:53:41-04:00 — S: keyframes (S04, S08, S09, S11, S13, S14, S15, S16, S17, S18, S19, S22, S27a, S27b, S27d, S27e, S28a, S28b, S31, S29v, S31v)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise 0.92 from the layout (v3 and later); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S04 S08 S09 S11 S13 S14 S15 S16 S17 S18 S19 S22 S27a S27b S27d S27e S28a S28b S31 S29v S31v`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S04_v4 | 2001 | renders/b/keyframe/S04/beauty/00000.png | `takes/keyframes/S04/S04_v4_s2001.png` | 77.1 | pending [H] |
| S04_v4 | 2002 | renders/b/keyframe/S04/beauty/00000.png | `takes/keyframes/S04/S04_v4_s2002.png` | 76.1 | pending [H] |
| S08_v4 | 2001 | renders/b/keyframe/S08/beauty/00509.png | `takes/keyframes/S08/S08_v4_s2001.png` | 77.1 | pending [H] |
| S08_v4 | 2002 | renders/b/keyframe/S08/beauty/00509.png | `takes/keyframes/S08/S08_v4_s2002.png` | 76.1 | kept ([H] approved 2026-10-20) |
| S09_v4 | 2002 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_v4_s2002.png` | 77.1 | pending [H] |
| S11_v4 | 2001 | renders/b/keyframe/S11/beauty/00826.png | `takes/keyframes/S11/S11_v4_s2001.png` | 77.1 | pending [H] |
| S11_v4 | 2002 | renders/b/keyframe/S11/beauty/00826.png | `takes/keyframes/S11/S11_v4_s2002.png` | 76.1 | pending [H] |
| S13_v4 | 2001 | renders/b/keyframe/S13/beauty/00980.png, takes/stills/kept/kid.png | `takes/keyframes/S13/S13_v4_s2001.png` | 107.2 | pending [H] |
| S13_v4 | 2002 | renders/b/keyframe/S13/beauty/00980.png, takes/stills/kept/kid.png | `takes/keyframes/S13/S13_v4_s2002.png` | 106.1 | pending [H] |
| S14_v4 | 2001 | renders/b/keyframe/S14/beauty/00993.png | `takes/keyframes/S14/S14_v4_s2001.png` | 77.1 | pending [H] |
| S14_v4 | 2002 | renders/b/keyframe/S14/beauty/00993.png | `takes/keyframes/S14/S14_v4_s2002.png` | 76.1 | kept ([H] approved 2026-10-20) |
| S15_v4 | 2002 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_v4_s2002.png` | 107.3 | pending [H] |
| S16_v4 | 2001 | renders/b/keyframe/S16/beauty/01308.png | `takes/keyframes/S16/S16_v4_s2001.png` | 77.1 | kept ([H] approved 2026-10-20) |
| S16_v4 | 2002 | renders/b/keyframe/S16/beauty/01308.png | `takes/keyframes/S16/S16_v4_s2002.png` | 76.1 | pending [H] |
| S17_v4 | 2001 | renders/b/keyframe/S17/beauty/01336.png, takes/stills/kept/grandma.png, takes/stills/kept/pie.png | `takes/keyframes/S17/S17_v4_s2001.png` | 148.3 | kept ([H] approved 2026-10-20) |
| S17_v4 | 2002 | renders/b/keyframe/S17/beauty/01336.png, takes/stills/kept/grandma.png, takes/stills/kept/pie.png | `takes/keyframes/S17/S17_v4_s2002.png` | 147.2 | pending [H] |
| S18_v4 | 2002 | renders/b/keyframe/S18/beauty/01556.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S18/S18_v4_s2002.png` | 107.1 | pending [H] |
| S19_v4 | 2001 | renders/b/keyframe/S19/beauty/01751.png, takes/stills/kept/singer.png | `takes/keyframes/S19/S19_v4_s2001.png` | 108.1 | kept ([H] approved 2026-10-20) |
| S19_v4 | 2002 | renders/b/keyframe/S19/beauty/01751.png, takes/stills/kept/singer.png | `takes/keyframes/S19/S19_v4_s2002.png` | 106.4 | pending [H] |
| S22_v4 | 2001 | renders/b/keyframe/S22/beauty/02050.png, takes/stills/kept/singer.png | `takes/keyframes/S22/S22_v4_s2001.png` | 107.1 | pending [H] |
| S22_v4 | 2002 | renders/b/keyframe/S22/beauty/02050.png, takes/stills/kept/singer.png | `takes/keyframes/S22/S22_v4_s2002.png` | 106.2 | pending [H] |
| S27a_v4 | 2001 | renders/b/keyframe/S27a/beauty/02320.png, takes/stills/kept/grandma.png | `takes/keyframes/S27a/S27a_v4_s2001.png` | 107.2 | pending [H] |
| S27a_v4 | 2002 | renders/b/keyframe/S27a/beauty/02320.png, takes/stills/kept/grandma.png | `takes/keyframes/S27a/S27a_v4_s2002.png` | 106.3 | pending [H] |
| S27b_v4 | 2001 | renders/b/keyframe/S27b/beauty/02331.png, takes/stills/kept/kid.png | `takes/keyframes/S27b/S27b_v4_s2001.png` | 107.3 | pending [H] |
| S27b_v4 | 2002 | renders/b/keyframe/S27b/beauty/02331.png, takes/stills/kept/kid.png | `takes/keyframes/S27b/S27b_v4_s2002.png` | 106.3 | kept ([H] approved 2026-10-20) |
| S27d_v4 | 2001 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_v4_s2001.png` | 77.2 | pending [H] |
| S27d_v4 | 2002 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_v4_s2002.png` | 76.3 | pending [H] |
| S27e_v4 | 2001 | renders/b/keyframe/S27e/beauty/02362.png | `takes/keyframes/S27e/S27e_v4_s2001.png` | 77.3 | pending [H] |
| S27e_v4 | 2002 | renders/b/keyframe/S27e/beauty/02362.png | `takes/keyframes/S27e/S27e_v4_s2002.png` | 76.4 | pending [H] |
| S28a_v4 | 2001 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v4_s2001.png` | 77.1 | pending [H] |
| S28a_v4 | 2002 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v4_s2002.png` | 76.1 | pending [H] |
| S28b_v4 | 2001 | renders/b/keyframe/S28b/beauty/02382.png | `takes/keyframes/S28b/S28b_v4_s2001.png` | 77.1 | pending [H] |
| S28b_v4 | 2002 | renders/b/keyframe/S28b/beauty/02382.png | `takes/keyframes/S28b/S28b_v4_s2002.png` | 76.1 | pending [H] |
| S31_v4 | 2001 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_v4_s2001.png` | 148.3 | pending [H] |
| S31_v4 | 2002 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_v4_s2002.png` | 146.5 | pending [H] |
| S29v_v4 | 2001 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v4_s2001.png` | 107.2 | pending [H] |
| S29v_v4 | 2002 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v4_s2002.png` | 106.4 | pending [H] |
| S31v_v4 | 2001 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v4_s2001.png` | 148.3 | pending [H] |
| S31v_v4 | 2002 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v4_s2002.png` | 147.2 | pending [H] |

## 2026-10-19T18:58:46-04:00 — S: keyframes (S11, S22, S27a, S28a, S29v, S31v)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise 0.92 from the layout (v3 and later); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S11 S22 S27a S28a S29v S31v`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S11_v5 | 2001 | renders/b/keyframe/S11/beauty/00826.png | `takes/keyframes/S11/S11_v5_s2001.png` | 79.2 | pending [H] |
| S11_v5 | 2002 | renders/b/keyframe/S11/beauty/00826.png | `takes/keyframes/S11/S11_v5_s2002.png` | 79.2 | pending [H] |
| S22_v5 | 2001 | renders/b/keyframe/S22/beauty/02050.png, takes/stills/kept/singer.png | `takes/keyframes/S22/S22_v5_s2001.png` | 111.4 | pending [H] |
| S22_v5 | 2002 | renders/b/keyframe/S22/beauty/02050.png, takes/stills/kept/singer.png | `takes/keyframes/S22/S22_v5_s2002.png` | 110.4 | pending [H] |
| S27a_v5 | 2001 | renders/b/keyframe/S27a/beauty/02320.png, takes/stills/kept/grandma.png | `takes/keyframes/S27a/S27a_v5_s2001.png` | 111.2 | pending [H] |
| S27a_v5 | 2002 | renders/b/keyframe/S27a/beauty/02320.png, takes/stills/kept/grandma.png | `takes/keyframes/S27a/S27a_v5_s2002.png` | 111.1 | kept ([H] approved 2026-10-20) |
| S28a_v5 | 2001 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v5_s2001.png` | 80.1 | pending [H] |
| S28a_v5 | 2002 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v5_s2002.png` | 79.2 | pending [H] |
| S29v_v5 | 2001 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v5_s2001.png` | 112.2 | pending [H] |
| S29v_v5 | 2002 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v5_s2002.png` | 110.4 | pending [H] |
| S31v_v5 | 2001 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v5_s2001.png` | 154.3 | pending [H] |
| S31v_v5 | 2002 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v5_s2002.png` | 152.3 | pending [H] |

## 2026-10-19T19:20:55-04:00 — S: keyframes (S11, S29v, S31v)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise 0.92 from the layout (v3 and later); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S11 S29v S31v`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S11_v6 | 2001 | renders/b/keyframe/S11/beauty/00826.png | `takes/keyframes/S11/S11_v6_s2001.png` | 82.3 | kept ([H] approved 2026-10-20) |
| S11_v6 | 2002 | renders/b/keyframe/S11/beauty/00826.png | `takes/keyframes/S11/S11_v6_s2002.png` | 275.4 | pending [H] |
| S29v_v6 | 2001 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v6_s2001.png` | 308.4 | pending [H] |
| S29v_v6 | 2002 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v6_s2002.png` | 263.4 | pending [H] |
| S31v_v6 | 2001 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v6_s2001.png` | 306.5 | pending [H] |
| S31v_v6 | 2002 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v6_s2002.png` | 266.4 | pending [H] |

## 2026-10-19T19:21:04-04:00 — S: keyframes (S05, S26, S29, S33)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise 0.92 from the layout (v3 and later); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S05 S26 S29 S33`

| Shot | Seed | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- |
| S05_v4 | 2001 | renders/b/keyframe/S05/beauty/00320.png, takes/stills/kept/singer.png, takes/stills/kept/dog.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S05/S05_v4_s2001.png` | 266.4 | pending [H] |
| S05_v4 | 2002 | renders/b/keyframe/S05/beauty/00320.png, takes/stills/kept/singer.png, takes/stills/kept/dog.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S05/S05_v4_s2002.png` | 275.7 | pending [H] |
| S26_v4 | 2001 | renders/b/keyframe/S26/beauty/02242.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S26/S26_v4_s2001.png` | 263.3 | pending [H] |
| S26_v4 | 2002 | renders/b/keyframe/S26/beauty/02242.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S26/S26_v4_s2002.png` | 264.4 | pending [H] |
| S29_v4 | 2001 | renders/b/keyframe/S29/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29/S29_v4_s2001.png` | 265.6 | pending [H] |
| S29_v4 | 2002 | renders/b/keyframe/S29/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29/S29_v4_s2002.png` | 267.4 | pending [H] |
| S33_v4 | 2001 | renders/b/keyframe/S33/beauty/03219.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S33/S33_v4_s2001.png` | 148.3 | pending [H] |
| S33_v4 | 2002 | renders/b/keyframe/S33/beauty/03219.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S33/S33_v4_s2002.png` | 148.3 | pending [H] |

### Note — keyframe picks for [H] (2026-10-19)

v5 (S11, S22, S27a, S28a, S29v, S31v): per-shot denoise 0.96, where 0.92 kept the stand-in blocks; the log table above records the config default, so these rows ran at 0.96. v6 (S11, S29v, S31v): denoise 1.0 (reference editing only). S05, S26, S29 and S33 were re-made at v4 (S05's pilot frame had teal posts; the others had extra people). The colour banding seen on S29v and S31v is in the scaled review grid only; the full frames are clean. Recommended picks, with flags for known weaknesses: `config/keyframe_picks.json`; contact sheet `takes/keyframes/picks_contact_sheet.png`. Status: pending [H].

## 2026-10-19T20:08:36-04:00 — S: keyframes (S27e, S31, S28b, S05, S04, S09, S13, S27d, S12, S28a, S06, S15, S22, S26, S29, S33, S29v, S31v)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise from the layout per row (v3 and later; 1.0 = none); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S27e S31 S28b S05 S04 S09 S13 S27d S12 S28a S06 S15 S22 S26 S29 S33 S29v S31v`

| Shot | Seed | Denoise | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| S27e_v7 | 2001 | 0.92 | renders/b/keyframe/S27e/beauty/02362.png | `takes/keyframes/S27e/S27e_v7_s2001.png` | 92.2 | kept ([H] approved 2026-10-20) |
| S27e_v7 | 2002 | 0.92 | renders/b/keyframe/S27e/beauty/02362.png | `takes/keyframes/S27e/S27e_v7_s2002.png` | 77.1 | rejected (agent review, see note) |
| S31_v7 | 2001 | 0.92 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_v7_s2001.png` | 149.2 | rejected (agent review, see note) |
| S31_v7 | 2002 | 0.92 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_v7_s2002.png` | 146.2 | rejected (agent review, see note) |
| S28b_v7 | 2001 | 0.92 | renders/b/keyframe/S28b/beauty/02382.png | `takes/keyframes/S28b/S28b_v7_s2001.png` | 77.1 | rejected (agent review, see note) |
| S28b_v7 | 2002 | 0.92 | renders/b/keyframe/S28b/beauty/02382.png | `takes/keyframes/S28b/S28b_v7_s2002.png` | 76.1 | kept ([H] approved 2026-10-20) |
| S05_v7 | 2001 | 0.96 | renders/b/keyframe/S05/beauty/00320.png, takes/stills/kept/singer.png, takes/stills/kept/dog.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S05/S05_v7_s2001.png` | 200.3 | rejected (agent review, see note) |
| S05_v7 | 2002 | 0.96 | renders/b/keyframe/S05/beauty/00320.png, takes/stills/kept/singer.png, takes/stills/kept/dog.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S05/S05_v7_s2002.png` | 199.3 | rejected (agent review, see note) |
| S04_v7 | 2001 | 0.92 | renders/b/keyframe/S04/beauty/00000.png | `takes/keyframes/S04/S04_v7_s2001.png` | 77.1 | rejected (agent review, see note) |
| S04_v7 | 2002 | 0.92 | renders/b/keyframe/S04/beauty/00000.png | `takes/keyframes/S04/S04_v7_s2002.png` | 76.1 | rejected (agent review, see note) |
| S09_v7 | 2001 | 0.92 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_v7_s2001.png` | 77.1 | rejected (agent review, see note) |
| S09_v7 | 2002 | 0.92 | renders/b/keyframe/S09/beauty/00572.png | `takes/keyframes/S09/S09_v7_s2002.png` | 76.1 | kept ([H] approved 2026-10-20) |
| S13_v7 | 2001 | 0.92 | renders/b/keyframe/S13/beauty/00980.png, takes/stills/kept/kid.png | `takes/keyframes/S13/S13_v7_s2001.png` | 107.3 | rejected (agent review, see note) |
| S13_v7 | 2002 | 0.92 | renders/b/keyframe/S13/beauty/00980.png, takes/stills/kept/kid.png | `takes/keyframes/S13/S13_v7_s2002.png` | 106.3 | rejected (agent review, see note) |
| S27d_v7 | 2001 | 0.92 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_v7_s2001.png` | 77.2 | rejected (agent review, see note) |
| S27d_v7 | 2002 | 0.92 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_v7_s2002.png` | 76.2 | rejected (agent review, see note) |
| S12_v7 | 2001 | 0.92 | renders/b/keyframe/S12/beauty/00880.png, takes/stills/kept/singer.png | `takes/keyframes/S12/S12_v7_s2001.png` | 107.3 | rejected (agent review, see note) |
| S12_v7 | 2002 | 0.92 | renders/b/keyframe/S12/beauty/00880.png, takes/stills/kept/singer.png | `takes/keyframes/S12/S12_v7_s2002.png` | 106.4 | superseded by v8 ([H]: Blender corn in the V take) |
| S28a_v7 | 2001 | 0.92 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v7_s2001.png` | 77.1 | rejected (agent review, see note) |
| S28a_v7 | 2002 | 0.92 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v7_s2002.png` | 76.1 | rejected (agent review, see note) |
| S06_v7 | 2001 | 0.96 | renders/b/keyframe/S06/beauty/00420.png, takes/stills/kept/dog.png, takes/stills/kept/singer.png | `takes/keyframes/S06/S06_v7_s2001.png` | 154.2 | rejected (agent review, see note) |
| S06_v7 | 2002 | 0.96 | renders/b/keyframe/S06/beauty/00420.png, takes/stills/kept/dog.png, takes/stills/kept/singer.png | `takes/keyframes/S06/S06_v7_s2002.png` | 153.2 | rejected ([H], 2026-10-20: Blender corn, seen in the V takes) |
| S15_v7 | 2001 | 0.96 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_v7_s2001.png` | 111.2 | rejected (agent review, see note) |
| S15_v7 | 2002 | 0.96 | renders/b/keyframe/S15/beauty/01143.png, takes/stills/kept/singer.png | `takes/keyframes/S15/S15_v7_s2002.png` | 111.1 | kept ([H] approved 2026-10-20) |
| S22_v7 | 2001 | 0.96 | renders/b/keyframe/S22/beauty/02050.png, takes/stills/kept/singer.png | `takes/keyframes/S22/S22_v7_s2001.png` | 111.4 | kept ([H] approved 2026-10-20) |
| S22_v7 | 2002 | 0.96 | renders/b/keyframe/S22/beauty/02050.png, takes/stills/kept/singer.png | `takes/keyframes/S22/S22_v7_s2002.png` | 111.1 | rejected (agent review, see note) |
| S26_v7 | 2001 | 0.96 | renders/b/keyframe/S26/beauty/02242.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S26/S26_v7_s2001.png` | 153.6 | rejected (agent review, see note) |
| S26_v7 | 2002 | 0.96 | renders/b/keyframe/S26/beauty/02242.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S26/S26_v7_s2002.png` | 153.2 | kept ([H] approved 2026-10-20) |
| S29_v7 | 2001 | 0.96 | renders/b/keyframe/S29/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29/S29_v7_s2001.png` | 111.4 | rejected (agent review, see note) |
| S29_v7 | 2002 | 0.96 | renders/b/keyframe/S29/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29/S29_v7_s2002.png` | 111.2 | rejected (agent review, see note) |
| S33_v7 | 2001 | 0.96 | renders/b/keyframe/S33/beauty/03219.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S33/S33_v7_s2001.png` | 154.2 | rejected (agent review, see note) |
| S33_v7 | 2002 | 0.96 | renders/b/keyframe/S33/beauty/03219.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S33/S33_v7_s2002.png` | 152.4 | rejected (agent review, see note) |
| S29v_v7 | 2001 | 0.96 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v7_s2001.png` | 111.4 | rejected (agent review, see note) |
| S29v_v7 | 2002 | 0.96 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v7_s2002.png` | 111.1 | rejected (agent review, see note) |
| S31v_v7 | 2001 | 0.96 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v7_s2001.png` | 154.2 | rejected (agent review, see note) |
| S31v_v7 | 2002 | 0.96 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v7_s2002.png` | 152.2 | superseded (later pick, see keyframe_picks.json) |

**Agent review of v7 (2026-10-19).** The four [H]-found fixes held: S05's flagpole leans from the post with the flag above the frame, S31's pie and mug rest on the rail (S31v s2002), S28b's tank is a cylinder under a conical roof, S27e's leash hangs straight down to the collar (s2001; s2002 reframed). Picks: S06 s2002 (the dog stands where its stand-in was; s2001 kept the beige block), S09 s2002 (s2001 added a power pole), S12 s2002 (s2001's corn stays blocky), S15 s2002, S22 s2001 (s2002 reframed), S26 s2002 (a real flag; s2001's flag stays a flat red sheet), S27e s2001, S28b s2002, S31v s2002 (s2001 reframed). Rejected, re-made at v8: S04 (s2001 dropped the bunting sign and the cranes, s2002 moved the tower), S05 (s2001 moved the dog, s2002 kept the dog's beige block), S13 (corn still blocky), S27d (the pale verge turned into a solid cream wall under the fence; stand-in cow blocks remain), S28a (a small church set in front of a blank white block instead of the block becoming the church), S29 and S29v (corn blocky, or gone), S31 (0.92 kept the blue stand-in tin and flat background; s2001 reframed), S33 (corn gone; s2002 kept the stand-in arm as a plank).

## 2026-10-19T21:20:31-04:00 — S: keyframes (S04, S05, S13, S27d, S28a, S29, S29v, S31, S33)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise from the layout per row (v3 and later; 1.0 = none); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S04 S05 S13 S27d S28a S29 S29v S31 S33`

| Shot | Seed | Denoise | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| S04_v8 | 2001 | 0.92 | renders/b/keyframe/S04/beauty/00000.png | `takes/keyframes/S04/S04_v8_s2001.png` | 76.1 | kept ([H] approved 2026-10-20) |
| S04_v8 | 2002 | 0.92 | renders/b/keyframe/S04/beauty/00000.png | `takes/keyframes/S04/S04_v8_s2002.png` | 76.1 | rejected (agent review, see note) |
| S05_v7 | 2003 | 0.96 | renders/b/keyframe/S05/beauty/00320.png, takes/stills/kept/singer.png, takes/stills/kept/dog.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S05/S05_v7_s2003.png` | 200.3 | rejected (agent review, see note) |
| S05_v7 | 2004 | 0.96 | renders/b/keyframe/S05/beauty/00320.png, takes/stills/kept/singer.png, takes/stills/kept/dog.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S05/S05_v7_s2004.png` | 198.6 | kept ([H] approved 2026-10-20) |
| S13_v8 | 2001 | 0.96 | renders/b/keyframe/S13/beauty/00980.png, takes/stills/kept/kid.png | `takes/keyframes/S13/S13_v8_s2001.png` | 111.4 | rejected (agent review, see note) |
| S13_v8 | 2002 | 0.96 | renders/b/keyframe/S13/beauty/00980.png, takes/stills/kept/kid.png | `takes/keyframes/S13/S13_v8_s2002.png` | 111.1 | kept ([H] approved 2026-10-20) |
| S27d_v8 | 2001 | 0.96 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_v8_s2001.png` | 80.2 | rejected (agent review, see note) |
| S27d_v8 | 2002 | 0.96 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_v8_s2002.png` | 79.3 | rejected (agent review, see note) |
| S28a_v8 | 2001 | 0.96 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v8_s2001.png` | 80.1 | rejected (agent review, see note) |
| S28a_v8 | 2002 | 0.96 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v8_s2002.png` | 79.2 | kept ([H] approved 2026-10-20) |
| S29_v8 | 2001 | 0.96 | renders/b/keyframe/S29/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29/S29_v8_s2001.png` | 112.1 | kept ([H] approved 2026-10-20) |
| S29_v8 | 2002 | 0.96 | renders/b/keyframe/S29/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29/S29_v8_s2002.png` | 110.4 | rejected (agent review, see note) |
| S29v_v8 | 2001 | 0.96 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v8_s2001.png` | 111.4 | rejected (agent review, see note) |
| S29v_v8 | 2002 | 0.96 | renders/b/keyframe/S29v/beauty/02392.png, takes/stills/kept/singer.png | `takes/keyframes/S29v/S29v_v8_s2002.png` | 111.1 | kept ([H] approved 2026-10-20) |
| S31_v7 | 2003 | 0.96 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_v7_s2003.png` | 154.2 | rejected (agent review, see note) |
| S31_v7 | 2004 | 0.96 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_v7_s2004.png` | 152.2 | superseded (later pick, see keyframe_picks.json) |
| S33_v8 | 2001 | 0.96 | renders/b/keyframe/S33/beauty/03219.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S33/S33_v8_s2001.png` | 154.5 | kept ([H] approved 2026-10-20) |
| S33_v8 | 2002 | 0.96 | renders/b/keyframe/S33/beauty/03219.png, takes/stills/kept/singer.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S33/S33_v8_s2002.png` | 153.3 | rejected (agent review, see note) |

## 2026-10-19T21:57:15-04:00 — S: keyframes (S27d)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise from the layout per row (v3 and later; 1.0 = none); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S27d`

| Shot | Seed | Denoise | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| S27d_v9 | 2001 | 0.96 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_v9_s2001.png` | 80.1 | rejected (agent review, see note) |
| S27d_v9 | 2002 | 0.96 | renders/b/keyframe/S27d/beauty/02352.png | `takes/keyframes/S27d/S27d_v9_s2002.png` | 80.1 | kept ([H] approved 2026-10-20) |

**Agent review of v8 and v9 (2026-10-19).** Picks: S04 v8 s2001 (bunting sign and cranes back; s2002 moved the tower), S05 v7 s2004 (the dog where its stand-in was, real corn; s2003 moved the dog), S13 v8 s2002 (real corn, the kid at the layout's size), S28a v8 s2002 (the whole massing is one church: nave, bell tower, side wing), S29 v8 s2001 (real corn, one raised hand as in the layout), S29v v8 s2002, S31 v7 s2004 at 0.96 (real tin, pie and mug on the rail; s2003 reframed), S33 v8 s2001, S27d v9 s2002 (v8 and v9 both fixed the cream wall under the fence; a few far stand-in cows still read as gray boxes). Flags for [H] are in `config/keyframe_picks.json`. Contact sheet: `.venv/bin/python scripts/picks_sheet.py` → `takes/keyframes/picks_contact_sheet.png`. Status: pending [H].

## 2026-10-20T05:20:49-04:00 — S: keyframes (S31, S31v)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise from the layout per row (v3 and later; 1.0 = none); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S31 S31v`

| Shot | Seed | Denoise | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| S31_v8 | 2001 | 0.96 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_v8_s2001.png` | 177.8 | rejected (agent review, see note) |
| S31_v8 | 2002 | 0.96 | renders/b/keyframe/S31/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31/S31_v8_s2002.png` | 152.6 | kept ([H] approved 2026-10-20) |
| S31v_v8 | 2001 | 0.96 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v8_s2001.png` | 155.3 | rejected (agent review, see note) |
| S31v_v8 | 2002 | 0.96 | renders/b/keyframe/S31v/beauty/02585.png, takes/stills/kept/pie.png, takes/stills/kept/mug_blank.png | `takes/keyframes/S31v/S31v_v8_s2002.png` | 153.3 | kept ([H] approved 2026-10-20) |

**S31 and S31v v8 (2026-10-20).** [H] rejected the S31 pie as looking like a dog bowl and traced it to the layout: the tin narrowed toward the top. The set now has a flared 9-inch tin with a lip and a domed pie (`scripts/blender/build_town.py`); both layouts re-rendered. Picks: S31 v8 s2002 and S31v v8 s2002, a lattice pie in a tin that widens to the rim, on the rail, with the layout held; s2001 reframed in both. A farmhouse with a gable and porch is soft in the background. `scripts/comfy_client.py` now uploads each image under its last three path parts, because S31 and S31v layouts share the file name `02585.png`. Status: pending [H].

## 2026-10-20T05:50:00-04:00 — V: control test on S05 (Blender depth vs MoGe), stage start

- **Plate:** `blender -b scenes/town.blend --python scripts/blender/render_shot.py -- S05 --frames 320:417 --res 1280x704 --samples 32 --out renders/b/test_v2` (56 s), passes encoded with `ffmpeg -framerate 24 -start_number 320 -i S05/<pass>/%05d.png -c:v libx264 -crf 12 -pix_fmt yuv420p`. First frame: the approved keyframe `takes/keyframes/S05/S05_v7_s2004.png`, scaled to 1280×704.
- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; 8 steps, euler_ancestral, cfg 1; 97 frames.
- **Prompt:** "Golden hour on a farmhouse porch. The smiling man in the red plaid flannel shirt stands still and holds the white coffee mug at his chest, then lifts it slightly; the golden retriever at his feet turns its head and looks off to the right. The cornfield beyond the porch sways gently in a light breeze. Very slow, steady push-in. Warm cinematic film look, shallow depth of field." Negative: `NEGATIVE` in `scripts/ltx_v.py` (the template's own negative banned smiling and eye contact).
- **Bug found:** `ltx_v.py` downloaded the first video in the graph's outputs, which was the control's preview, so both first downloads looked like their inputs. It now takes SaveVideo (node 68). This was also the cause of the pre-production finding "Blender depth reproduces the gray depth image"; `style/vram_plan.md` is corrected.

| Test | Seed | Control | Time | GPU peak | RAM peak | Swap peak | Output | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S05 | 1 | Blender depth (`--control depth`) | 45.3 s | 31.9 GB | 36.6 GB | 7.4 GB | `takes/v/test/S05_ctl_depth.mp4` | test; method kept |
| S05 | 1 | MoGe on the Blender beauty (`--control moge`) | 45.3 s | 31.7 GB | 36.1 GB | 7.4 GB | `takes/v/test/S05_ctl_moge.mp4` | test |

- **Decision:** V uses the Blender depth pass as the control. The two takes are near-identical; the depth pass is the set's exact geometry with no estimation step.

## 2026-10-20T06:05:00-04:00 — B: V plates for all 29 V shots

- **What:** Each V shot's frames plus handles up to its clip plan (`scripts/v_batch.py`: LTX clips are 8n+1 frames, at most 97, chained), 1280×704 (verticals 704×1280), Eevee 32 samples, all passes; V uses the depth pass. 2,885 frames.
- **Command:** `.venv/bin/python scripts/v_batch.py plates --jobs 4` → `renders/b/v_plates/<shot>/` (git-ignored, regenerable). S04 was rendered first with one process (one Blender keeps the GPU at about 25%, 106 W, CPU-bound), the other 28 four at a time (about 3.8 frames/s instead of 1.7; CPU about 80% busy, GPU about 36%). Per-shot times: 10 s (S28a) to 170 s (S17).
- **Status:** kept (plates are inputs, not takes).

## 2026-10-20T06:10:00-04:00 — V: shots (all 29; stopped after S08)

- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; template `comfy/api/video_ltx2_3_ic_lora.api.json`; 8 steps, euler_ancestral, cfg 1; 1280×704. Control: the Blender depth pass. First frame: the approved keyframe (clip 0) or the previous clip's last frame.
- **Prompts:** `config/v.json` (shot prompt + style); negative `NEGATIVE` in `scripts/ltx_v.py`. **Command:** `.venv/bin/python scripts/v_batch.py gen` (seeds 1, 2).
- **Stopped:** Claude Code's memory guard stopped ComfyUI and the batch while S09 was generating (RAM 35 of 38 GB and 7 GB of swap is this stage's normal load). S04, S05, S06 and S08 finished for both seeds; S09's partial clips are re-made on resume. The batch wrote its log rows only at the end, so these rows are backfilled from the files, without clip times; `v_batch.py` now logs each clip as it finishes.

| Shot | Seed | Clip | Plate frames | Control | First frame | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S04 | 1 | 0 | 0-96 | `takes/v/S04/S04_s1_c0_depth.mp4` | `takes/v/S04/S04_s1_c0_first.png` | `takes/v/S04/S04_s1_c0.mp4` | — | kept ([H] approved 2026-10-20) |
| S04 | 1 | 1 | 96-192 | `takes/v/S04/S04_s1_c1_depth.mp4` | `takes/v/S04/S04_s1_c1_first.png` | `takes/v/S04/S04_s1_c1.mp4` | — | kept ([H] approved 2026-10-20) |
| S04 | 1 | 2 | 192-288 | `takes/v/S04/S04_s1_c2_depth.mp4` | `takes/v/S04/S04_s1_c2_first.png` | `takes/v/S04/S04_s1_c2.mp4` | — | kept ([H] approved 2026-10-20) |
| S04 | 1 | 3 | 288-320 | `takes/v/S04/S04_s1_c3_depth.mp4` | `takes/v/S04/S04_s1_c3_first.png` | `takes/v/S04/S04_s1_c3.mp4` | — | kept ([H] approved 2026-10-20) |
| S04 | 2 | 0 | 0-96 | `takes/v/S04/S04_s2_c0_depth.mp4` | `takes/v/S04/S04_s2_c0_first.png` | `takes/v/S04/S04_s2_c0.mp4` | — | rejected (agent review: the other seed is the pick) |
| S04 | 2 | 1 | 96-192 | `takes/v/S04/S04_s2_c1_depth.mp4` | `takes/v/S04/S04_s2_c1_first.png` | `takes/v/S04/S04_s2_c1.mp4` | — | rejected (agent review: the other seed is the pick) |
| S04 | 2 | 2 | 192-288 | `takes/v/S04/S04_s2_c2_depth.mp4` | `takes/v/S04/S04_s2_c2_first.png` | `takes/v/S04/S04_s2_c2.mp4` | — | rejected (agent review: the other seed is the pick) |
| S04 | 2 | 3 | 288-320 | `takes/v/S04/S04_s2_c3_depth.mp4` | `takes/v/S04/S04_s2_c3_first.png` | `takes/v/S04/S04_s2_c3.mp4` | — | rejected (agent review: the other seed is the pick) |
| S05 | 1 | 0 | 320-416 | `takes/v/S05/S05_s1_c0_depth.mp4` | `takes/v/S05/S05_s1_c0_first.png` | `takes/v/S05/S05_s1_c0.mp4` | — | kept ([H] approved 2026-10-20) |
| S05 | 1 | 1 | 416-424 | `takes/v/S05/S05_s1_c1_depth.mp4` | `takes/v/S05/S05_s1_c1_first.png` | `takes/v/S05/S05_s1_c1.mp4` | — | kept ([H] approved 2026-10-20) |
| S05 | 2 | 0 | 320-416 | `takes/v/S05/S05_s2_c0_depth.mp4` | `takes/v/S05/S05_s2_c0_first.png` | `takes/v/S05/S05_s2_c0.mp4` | — | rejected (agent review: the other seed is the pick) |
| S05 | 2 | 1 | 416-424 | `takes/v/S05/S05_s2_c1_depth.mp4` | `takes/v/S05/S05_s2_c1_first.png` | `takes/v/S05/S05_s2_c1.mp4` | — | rejected (agent review: the other seed is the pick) |
| S06 | 1 | 0 | 420-452 | `takes/v/S06/S06_s1_c0_depth.mp4` | `takes/v/S06/S06_s1_c0_first.png` | `takes/v/S06/S06_s1_c0.mp4` | — | rejected ([H]: the keyframe's Blender corn; moved to takes/v/S06/rejected_kf_v7/) |
| S06 | 2 | 0 | 420-452 | `takes/v/S06/S06_s2_c0_depth.mp4` | `takes/v/S06/S06_s2_c0_first.png` | `takes/v/S06/S06_s2_c0.mp4` | — | rejected ([H]: the keyframe's Blender corn; moved to takes/v/S06/rejected_kf_v7/) |
| S08 | 1 | 0 | 509-573 | `takes/v/S08/S08_s1_c0_depth.mp4` | `takes/v/S08/S08_s1_c0_first.png` | `takes/v/S08/S08_s1_c0.mp4` | — | kept ([H] approved 2026-10-20) |
| S08 | 2 | 0 | 509-573 | `takes/v/S08/S08_s2_c0_depth.mp4` | `takes/v/S08/S08_s2_c0_first.png` | `takes/v/S08/S08_s2_c0.mp4` | — | rejected (agent review: the other seed is the pick) |

- **Join fix (2026-10-20):** the template generates at 25 fps, and the join re-timed the clips to 24 fps by time, dropping frames (S04 came out at 309 of 320). The clips themselves were complete. `ltx_v.py` now sets the frame rate to 24, and `v_batch.py`'s join re-times frames by index. S04, S05, S06 and S08 were re-joined from their clips and now have exactly their shots' frames (320, 100, 30, 63). Those four were generated with the model told 25 fps, so their motion plays about 4% slower than generated; not visible.

## 2026-10-20T06:28:09-04:00 — S: keyframes (S06)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise from the layout per row (v3 and later; 1.0 = none); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S06`

| Shot | Seed | Denoise | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| S06_v8 | 2001 | 0.96 | renders/b/keyframe/S06/beauty/00420.png, takes/stills/kept/dog.png, takes/stills/kept/singer.png | `takes/keyframes/S06/S06_v8_s2001.png` | 164.3 | rejected (agent review: kept the beige dog block) |
| S06_v8 | 2002 | 0.96 | renders/b/keyframe/S06/beauty/00420.png, takes/stills/kept/dog.png, takes/stills/kept/singer.png | `takes/keyframes/S06/S06_v8_s2002.png` | 152.2 | kept ([H] approved 2026-10-20) |

**S06 v8 (2026-10-20).** [H] saw Blender corn in both S06 V takes; it came from the v7 keyframe, whose prompt said only "cornfield beyond". v8 describes the cornfield as S05's prompt does. Pick: s2002 (real corn, the dog where its stand-in was); s2001 kept the beige dog block. S06's V takes are re-made from it.

## 2026-10-20T06:33:49-04:00 — V: shots (S04, S05, S06, S08, S09, S11, S12, S13, S14, S15, S16, S17, S18, S19, S20, S22, S26, S27a, S27b, S27c, S27d, S27e, S28a, S28b, S29, S31, S33, S29v, S31v)

- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; template `comfy/api/video_ltx2_3_ic_lora.api.json`; 8 steps, euler_ancestral, cfg 1; 1280×704. Control: the Blender depth pass. First frame: the approved keyframe (clip 0) or the previous clip's last frame.
- **Prompts:** `config/v.json` (shot prompt + style); negative `NEGATIVE` in `scripts/ltx_v.py`. **Command:** `.venv/bin/python scripts/v_batch.py gen S04 S05 S06 S08 S09 S11 S12 S13 S14 S15 S16 S17 S18 S19 S20 S22 S26 S27a S27b S27c S27d S27e S28a S28b S29 S31 S33 S29v S31v --seeds 1,2`

| Shot | Seed | Clip | Plate frames | Control | First frame | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S06 | 1 | 0 | 420-452 | `takes/v/S06/S06_s1_c0_depth.mp4` | `takes/v/S06/S06_s1_c0_first.png` | `takes/v/S06/S06_s1_c0.mp4` | 49.2 | kept ([H] approved 2026-10-20) |
| S06 | 2 | 0 | 420-452 | `takes/v/S06/S06_s2_c0_depth.mp4` | `takes/v/S06/S06_s2_c0_first.png` | `takes/v/S06/S06_s2_c0.mp4` | 11.0 | rejected (agent review: the other seed is the pick) |
| S09 | 1 | 0 | 572-668 | `takes/v/S09/S09_s1_c0_depth.mp4` | `takes/v/S09/S09_s1_c0_first.png` | `takes/v/S09/S09_s1_c0.mp4` | 28.1 | rejected (agent review: bunting lost from the sign) |
| S09 | 1 | 1 | 668-764 | `takes/v/S09/S09_s1_c1_depth.mp4` | `takes/v/S09/S09_s1_c1_first.png` | `takes/v/S09/S09_s1_c1.mp4` | 28.1 | rejected (agent review: bunting lost from the sign) |
| S09 | 1 | 2 | 764-772 | `takes/v/S09/S09_s1_c2_depth.mp4` | `takes/v/S09/S09_s1_c2_first.png` | `takes/v/S09/S09_s1_c2.mp4` | 6.0 | rejected (agent review: bunting lost from the sign) |
| S09 | 2 | 0 | 572-668 | `takes/v/S09/S09_s2_c0_depth.mp4` | `takes/v/S09/S09_s2_c0_first.png` | `takes/v/S09/S09_s2_c0.mp4` | 32.2 | rejected (agent review: bunting lost, plot became a parking lot) |
| S09 | 2 | 1 | 668-764 | `takes/v/S09/S09_s2_c1_depth.mp4` | `takes/v/S09/S09_s2_c1_first.png` | `takes/v/S09/S09_s2_c1.mp4` | 31.2 | rejected (agent review: bunting lost, plot became a parking lot) |
| S09 | 2 | 2 | 764-772 | `takes/v/S09/S09_s2_c2_depth.mp4` | `takes/v/S09/S09_s2_c2_first.png` | `takes/v/S09/S09_s2_c2.mp4` | 6.0 | rejected (agent review: bunting lost, plot became a parking lot) |
| S11 | 1 | 0 | 826-882 | `takes/v/S11/S11_s1_c0_depth.mp4` | `takes/v/S11/S11_s1_c0_first.png` | `takes/v/S11/S11_s1_c0.mp4` | 19.2 | kept ([H] approved 2026-10-20) |
| S11 | 2 | 0 | 826-882 | `takes/v/S11/S11_s2_c0_depth.mp4` | `takes/v/S11/S11_s2_c0_first.png` | `takes/v/S11/S11_s2_c0.mp4` | 17.1 | rejected (agent review: the other seed is the pick) |
| S12 | 1 | 0 | 880-976 | `takes/v/S12/S12_s1_c0_depth.mp4` | `takes/v/S12/S12_s1_c0_first.png` | `takes/v/S12/S12_s1_c0.mp4` | 28.2 | rejected ([H]: stiff walk, Blender corn); moved to `rejected_h_review/` |
| S12 | 1 | 1 | 976-984 | `takes/v/S12/S12_s1_c1_depth.mp4` | `takes/v/S12/S12_s1_c1_first.png` | `takes/v/S12/S12_s1_c1.mp4` | 6.0 | rejected ([H]: stiff walk, Blender corn); moved to `rejected_h_review/` |
| S12 | 2 | 0 | 880-976 | `takes/v/S12/S12_s2_c0_depth.mp4` | `takes/v/S12/S12_s2_c0_first.png` | `takes/v/S12/S12_s2_c0.mp4` | 27.1 | rejected ([H]: stiff walk, Blender corn); moved to `rejected_h_review/` |
| S12 | 2 | 1 | 976-984 | `takes/v/S12/S12_s2_c1_depth.mp4` | `takes/v/S12/S12_s2_c1_first.png` | `takes/v/S12/S12_s2_c1.mp4` | 6.0 | rejected ([H]: stiff walk, Blender corn); moved to `rejected_h_review/` |
| S13 | 1 | 0 | 980-996 | `takes/v/S13/S13_s1_c0_depth.mp4` | `takes/v/S13/S13_s1_c0_first.png` | `takes/v/S13/S13_s1_c0.mp4` | 7.0 | kept ([H] approved 2026-10-20) |
| S13 | 2 | 0 | 980-996 | `takes/v/S13/S13_s2_c0_depth.mp4` | `takes/v/S13/S13_s2_c0_first.png` | `takes/v/S13/S13_s2_c0.mp4` | 7.0 | rejected (agent review: the other seed is the pick) |
| S14 | 1 | 0 | 993-1089 | `takes/v/S14/S14_s1_c0_depth.mp4` | `takes/v/S14/S14_s1_c0_first.png` | `takes/v/S14/S14_s1_c0.mp4` | 29.6 | rejected (agent review: leaves blow across like embers) |
| S14 | 1 | 1 | 1089-1145 | `takes/v/S14/S14_s1_c1_depth.mp4` | `takes/v/S14/S14_s1_c1_first.png` | `takes/v/S14/S14_s1_c1.mp4` | 17.0 | rejected (agent review: leaves blow across like embers) |
| S14 | 2 | 0 | 993-1089 | `takes/v/S14/S14_s2_c0_depth.mp4` | `takes/v/S14/S14_s2_c0_first.png` | `takes/v/S14/S14_s2_c0.mp4` | 31.1 | rejected (agent review: leaves blow across like embers) |
| S14 | 2 | 1 | 1089-1145 | `takes/v/S14/S14_s2_c1_depth.mp4` | `takes/v/S14/S14_s2_c1_first.png` | `takes/v/S14/S14_s2_c1.mp4` | 20.0 | rejected (agent review: leaves blow across like embers) |
| S15 | 1 | 0 | 1143-1239 | `takes/v/S15/S15_s1_c0_depth.mp4` | `takes/v/S15/S15_s1_c0_first.png` | `takes/v/S15/S15_s1_c0.mp4` | 30.1 | kept ([H] approved 2026-10-20) |
| S15 | 1 | 1 | 1239-1311 | `takes/v/S15/S15_s1_c1_depth.mp4` | `takes/v/S15/S15_s1_c1_first.png` | `takes/v/S15/S15_s1_c1.mp4` | 21.0 | kept ([H] approved 2026-10-20) |
| S15 | 2 | 0 | 1143-1239 | `takes/v/S15/S15_s2_c0_depth.mp4` | `takes/v/S15/S15_s2_c0_first.png` | `takes/v/S15/S15_s2_c0.mp4` | 30.3 | rejected (agent review: the other seed is the pick) |
| S15 | 2 | 1 | 1239-1311 | `takes/v/S15/S15_s2_c1_depth.mp4` | `takes/v/S15/S15_s2_c1_first.png` | `takes/v/S15/S15_s2_c1.mp4` | 22.0 | rejected (agent review: the other seed is the pick) |
| S16 | 1 | 0 | 1308-1340 | `takes/v/S16/S16_s1_c0_depth.mp4` | `takes/v/S16/S16_s1_c0_first.png` | `takes/v/S16/S16_s1_c0.mp4` | 11.0 | kept ([H] approved 2026-10-20) |
| S16 | 2 | 0 | 1308-1340 | `takes/v/S16/S16_s2_c0_depth.mp4` | `takes/v/S16/S16_s2_c0_first.png` | `takes/v/S16/S16_s2_c0.mp4` | 10.4 | rejected (agent review: the plane bursts into a fireball) |
| S17 | 1 | 0 | 1336-1432 | `takes/v/S17/S17_s1_c0_depth.mp4` | `takes/v/S17/S17_s1_c0_first.png` | `takes/v/S17/S17_s1_c0.mp4` | 28.1 | rejected ([H]: grandma never moves); moved to `rejected_h_review/` |
| S17 | 1 | 1 | 1432-1528 | `takes/v/S17/S17_s1_c1_depth.mp4` | `takes/v/S17/S17_s1_c1_first.png` | `takes/v/S17/S17_s1_c1.mp4` | 31.1 | rejected ([H]: grandma never moves); moved to `rejected_h_review/` |
| S17 | 1 | 2 | 1528-1560 | `takes/v/S17/S17_s1_c2_depth.mp4` | `takes/v/S17/S17_s1_c2_first.png` | `takes/v/S17/S17_s1_c2.mp4` | 11.0 | rejected ([H]: grandma never moves); moved to `rejected_h_review/` |
| S17 | 2 | 0 | 1336-1432 | `takes/v/S17/S17_s2_c0_depth.mp4` | `takes/v/S17/S17_s2_c0_first.png` | `takes/v/S17/S17_s2_c0.mp4` | 28.3 | rejected ([H]: grandma never moves); moved to `rejected_h_review/` |
| S17 | 2 | 1 | 1432-1528 | `takes/v/S17/S17_s2_c1_depth.mp4` | `takes/v/S17/S17_s2_c1_first.png` | `takes/v/S17/S17_s2_c1.mp4` | 29.1 | rejected ([H]: grandma never moves); moved to `rejected_h_review/` |
| S17 | 2 | 2 | 1528-1560 | `takes/v/S17/S17_s2_c2_depth.mp4` | `takes/v/S17/S17_s2_c2_first.png` | `takes/v/S17/S17_s2_c2.mp4` | 11.0 | rejected ([H]: grandma never moves); moved to `rejected_h_review/` |
| S18 | 1 | 0 | 1556-1652 | `takes/v/S18/S18_s1_c0_depth.mp4` | `takes/v/S18/S18_s1_c0_first.png` | `takes/v/S18/S18_s1_c0.mp4` | 29.1 | kept ([H] approved 2026-10-20) |
| S18 | 1 | 1 | 1652-1748 | `takes/v/S18/S18_s1_c1_depth.mp4` | `takes/v/S18/S18_s1_c1_first.png` | `takes/v/S18/S18_s1_c1.mp4` | 28.5 | kept ([H] approved 2026-10-20) |
| S18 | 1 | 2 | 1748-1756 | `takes/v/S18/S18_s1_c2_depth.mp4` | `takes/v/S18/S18_s1_c2_first.png` | `takes/v/S18/S18_s1_c2.mp4` | 6.0 | kept ([H] approved 2026-10-20) |
| S18 | 2 | 0 | 1556-1652 | `takes/v/S18/S18_s2_c0_depth.mp4` | `takes/v/S18/S18_s2_c0_first.png` | `takes/v/S18/S18_s2_c0.mp4` | 27.1 | rejected (agent review: goes dark abruptly, a hand enters) |
| S18 | 2 | 1 | 1652-1748 | `takes/v/S18/S18_s2_c1_depth.mp4` | `takes/v/S18/S18_s2_c1_first.png` | `takes/v/S18/S18_s2_c1.mp4` | 32.1 | rejected (agent review: goes dark abruptly, a hand enters) |
| S18 | 2 | 2 | 1748-1756 | `takes/v/S18/S18_s2_c2_depth.mp4` | `takes/v/S18/S18_s2_c2_first.png` | `takes/v/S18/S18_s2_c2.mp4` | 6.0 | rejected (agent review: goes dark abruptly, a hand enters) |
| S19 | 1 | 0 | 1751-1831 | `takes/v/S19/S19_s1_c0_depth.mp4` | `takes/v/S19/S19_s1_c0_first.png` | `takes/v/S19/S19_s1_c0.mp4` | 23.0 | rejected ([H]: hand wrong); moved to `rejected_h_review/` |
| S19 | 2 | 0 | 1751-1831 | `takes/v/S19/S19_s2_c0_depth.mp4` | `takes/v/S19/S19_s2_c0_first.png` | `takes/v/S19/S19_s2_c0.mp4` | 24.0 | rejected ([H]: hand wrong); moved to `rejected_h_review/` |
| S20 | 1 | 0 | 1829-1925 | `takes/v/S20/S20_s1_c0_depth.mp4` | `takes/v/S20/S20_s1_c0_first.png` | `takes/v/S20/S20_s1_c0.mp4` | 30.1 | rejected (agent review: the other seed is the pick) |
| S20 | 1 | 1 | 1925-1989 | `takes/v/S20/S20_s1_c1_depth.mp4` | `takes/v/S20/S20_s1_c1_first.png` | `takes/v/S20/S20_s1_c1.mp4` | 19.0 | rejected (agent review: the other seed is the pick) |
| S20 | 2 | 0 | 1829-1925 | `takes/v/S20/S20_s2_c0_depth.mp4` | `takes/v/S20/S20_s2_c0_first.png` | `takes/v/S20/S20_s2_c0.mp4` | 32.1 | kept ([H] approved 2026-10-20) |
| S20 | 2 | 1 | 1925-1989 | `takes/v/S20/S20_s2_c1_depth.mp4` | `takes/v/S20/S20_s2_c1_first.png` | `takes/v/S20/S20_s2_c1.mp4` | 18.3 | kept ([H] approved 2026-10-20) |
| S22 | 1 | 0 | 2050-2090 | `takes/v/S22/S22_s1_c0_depth.mp4` | `takes/v/S22/S22_s1_c0_first.png` | `takes/v/S22/S22_s1_c0.mp4` | 14.4 | rejected (agent review: the point turns into an open palm) |
| S22 | 2 | 0 | 2050-2090 | `takes/v/S22/S22_s2_c0_depth.mp4` | `takes/v/S22/S22_s2_c0_first.png` | `takes/v/S22/S22_s2_c0.mp4` | 12.3 | kept ([H] approved 2026-10-20) |
| S26 | 1 | 0 | 2242-2322 | `takes/v/S26/S26_s1_c0_depth.mp4` | `takes/v/S26/S26_s1_c0_first.png` | `takes/v/S26/S26_s1_c0.mp4` | 23.4 | kept ([H] approved 2026-10-20) |
| S26 | 2 | 0 | 2242-2322 | `takes/v/S26/S26_s2_c0_depth.mp4` | `takes/v/S26/S26_s2_c0_first.png` | `takes/v/S26/S26_s2_c0.mp4` | 27.4 | rejected (agent review: the other seed is the pick) |
| S27a | 1 | 0 | 2320-2336 | `takes/v/S27a/S27a_s1_c0_depth.mp4` | `takes/v/S27a/S27a_s1_c0_first.png` | `takes/v/S27a/S27a_s1_c0.mp4` | 7.0 | kept ([H] approved 2026-10-20) |
| S27a | 2 | 0 | 2320-2336 | `takes/v/S27a/S27a_s2_c0_depth.mp4` | `takes/v/S27a/S27a_s2_c0_first.png` | `takes/v/S27a/S27a_s2_c0.mp4` | 7.0 | rejected (agent review: the other seed is the pick) |
| S27b | 1 | 0 | 2331-2347 | `takes/v/S27b/S27b_s1_c0_depth.mp4` | `takes/v/S27b/S27b_s1_c0_first.png` | `takes/v/S27b/S27b_s1_c0.mp4` | 7.0 | kept ([H] approved 2026-10-20) |
| S27b | 2 | 0 | 2331-2347 | `takes/v/S27b/S27b_s2_c0_depth.mp4` | `takes/v/S27b/S27b_s2_c0_first.png` | `takes/v/S27b/S27b_s2_c0.mp4` | 7.0 | rejected (agent review: the other seed is the pick) |
| S27c | 1 | 0 | 2341-2357 | `takes/v/S27c/S27c_s1_c0_depth.mp4` | `takes/v/S27c/S27c_s1_c0_first.png` | `takes/v/S27c/S27c_s1_c0.mp4` | 7.0 | kept ([H] approved 2026-10-20) |
| S27c | 2 | 0 | 2341-2357 | `takes/v/S27c/S27c_s2_c0_depth.mp4` | `takes/v/S27c/S27c_s2_c0_first.png` | `takes/v/S27c/S27c_s2_c0.mp4` | 7.0 | rejected (agent review: the other seed is the pick) |
| S27d | 1 | 0 | 2352-2368 | `takes/v/S27d/S27d_s1_c0_depth.mp4` | `takes/v/S27d/S27d_s1_c0_first.png` | `takes/v/S27d/S27d_s1_c0.mp4` | 7.0 | kept ([H] approved 2026-10-20) |
| S27d | 2 | 0 | 2352-2368 | `takes/v/S27d/S27d_s2_c0_depth.mp4` | `takes/v/S27d/S27d_s2_c0_first.png` | `takes/v/S27d/S27d_s2_c0.mp4` | 7.1 | rejected (agent review: the other seed is the pick) |
| S27e | 1 | 0 | 2362-2378 | `takes/v/S27e/S27e_s1_c0_depth.mp4` | `takes/v/S27e/S27e_s1_c0_first.png` | `takes/v/S27e/S27e_s1_c0.mp4` | 7.0 | kept ([H] approved 2026-10-20) |
| S27e | 2 | 0 | 2362-2378 | `takes/v/S27e/S27e_s2_c0_depth.mp4` | `takes/v/S27e/S27e_s2_c0_first.png` | `takes/v/S27e/S27e_s2_c0.mp4` | 7.0 | rejected (agent review: the other seed is the pick) |
| S28a | 1 | 0 | 2373-2381 | `takes/v/S28a/S28a_s1_c0_depth.mp4` | `takes/v/S28a/S28a_s1_c0_first.png` | `takes/v/S28a/S28a_s1_c0.mp4` | 6.0 | kept ([H] approved 2026-10-20) |
| S28a | 2 | 0 | 2373-2381 | `takes/v/S28a/S28a_s2_c0_depth.mp4` | `takes/v/S28a/S28a_s2_c0_first.png` | `takes/v/S28a/S28a_s2_c0.mp4` | 6.0 | rejected (agent review: leaves blow across like embers) |
| S28b | 1 | 0 | 2382-2398 | `takes/v/S28b/S28b_s1_c0_depth.mp4` | `takes/v/S28b/S28b_s1_c0_first.png` | `takes/v/S28b/S28b_s1_c0.mp4` | 7.0 | kept ([H] approved 2026-10-20) |
| S28b | 2 | 0 | 2382-2398 | `takes/v/S28b/S28b_s2_c0_depth.mp4` | `takes/v/S28b/S28b_s2_c0_first.png` | `takes/v/S28b/S28b_s2_c0.mp4` | 7.0 | rejected (agent review: the other seed is the pick) |
| S29 | 1 | 0 | 2392-2488 | `takes/v/S29/S29_s1_c0_depth.mp4` | `takes/v/S29/S29_s1_c0_first.png` | `takes/v/S29/S29_s1_c0.mp4` | 29.1 | rejected (agent review: the V drops to one finger at the end) |
| S29 | 1 | 1 | 2488-2552 | `takes/v/S29/S29_s1_c1_depth.mp4` | `takes/v/S29/S29_s1_c1_first.png` | `takes/v/S29/S29_s1_c1.mp4` | 21.1 | rejected (agent review: the V drops to one finger at the end) |
| S29 | 2 | 0 | 2392-2488 | `takes/v/S29/S29_s2_c0_depth.mp4` | `takes/v/S29/S29_s2_c0_first.png` | `takes/v/S29/S29_s2_c0.mp4` | 29.6 | rejected (agent review: a second ghost hand) |
| S29 | 2 | 1 | 2488-2552 | `takes/v/S29/S29_s2_c1_depth.mp4` | `takes/v/S29/S29_s2_c1_first.png` | `takes/v/S29/S29_s2_c1.mp4` | 20.0 | rejected (agent review: a second ghost hand) |
| S31 | 1 | 0 | 2585-2681 | `takes/v/S31/S31_s1_c0_depth.mp4` | `takes/v/S31/S31_s1_c0_first.png` | `takes/v/S31/S31_s1_c0.mp4` | 28.1 | kept ([H] approved 2026-10-20) |
| S31 | 1 | 1 | 2681-2697 | `takes/v/S31/S31_s1_c1_depth.mp4` | `takes/v/S31/S31_s1_c1_first.png` | `takes/v/S31/S31_s1_c1.mp4` | 7.0 | kept ([H] approved 2026-10-20) |
| S31 | 2 | 0 | 2585-2681 | `takes/v/S31/S31_s2_c0_depth.mp4` | `takes/v/S31/S31_s2_c0_first.png` | `takes/v/S31/S31_s2_c0.mp4` | 28.3 | rejected (agent review: the other seed is the pick) |
| S31 | 2 | 1 | 2681-2697 | `takes/v/S31/S31_s2_c1_depth.mp4` | `takes/v/S31/S31_s2_c1_first.png` | `takes/v/S31/S31_s2_c1.mp4` | 7.0 | rejected (agent review: the other seed is the pick) |
| S33 | 1 | 0 | 3219-3315 | `takes/v/S33/S33_s1_c0_depth.mp4` | `takes/v/S33/S33_s1_c0_first.png` | `takes/v/S33/S33_s1_c0.mp4` | 27.5 | kept ([H] approved 2026-10-20) |
| S33 | 1 | 1 | 3315-3395 | `takes/v/S33/S33_s1_c1_depth.mp4` | `takes/v/S33/S33_s1_c1_first.png` | `takes/v/S33/S33_s1_c1.mp4` | 23.1 | kept ([H] approved 2026-10-20) |
| S33 | 2 | 0 | 3219-3315 | `takes/v/S33/S33_s2_c0_depth.mp4` | `takes/v/S33/S33_s2_c0_first.png` | `takes/v/S33/S33_s2_c0.mp4` | 28.1 | rejected (agent review: the other seed is the pick) |
| S33 | 2 | 1 | 3315-3395 | `takes/v/S33/S33_s2_c1_depth.mp4` | `takes/v/S33/S33_s2_c1_first.png` | `takes/v/S33/S33_s2_c1.mp4` | 23.4 | rejected (agent review: the other seed is the pick) |
| S29v | 1 | 0 | 2392-2488 | `takes/v/S29v/S29v_s1_c0_depth.mp4` | `takes/v/S29v/S29v_s1_c0_first.png` | `takes/v/S29v/S29v_s1_c0.mp4` | 30.1 | rejected (agent review: the other seed is the pick) |
| S29v | 1 | 1 | 2488-2552 | `takes/v/S29v/S29v_s1_c1_depth.mp4` | `takes/v/S29v/S29v_s1_c1_first.png` | `takes/v/S29v/S29v_s1_c1.mp4` | 21.1 | rejected (agent review: the other seed is the pick) |
| S29v | 2 | 0 | 2392-2488 | `takes/v/S29v/S29v_s2_c0_depth.mp4` | `takes/v/S29v/S29v_s2_c0_first.png` | `takes/v/S29v/S29v_s2_c0.mp4` | 29.1 | kept ([H] approved 2026-10-20) |
| S29v | 2 | 1 | 2488-2552 | `takes/v/S29v/S29v_s2_c1_depth.mp4` | `takes/v/S29v/S29v_s2_c1_first.png` | `takes/v/S29v/S29v_s2_c1.mp4` | 20.1 | kept ([H] approved 2026-10-20) |
| S31v | 1 | 0 | 2585-2681 | `takes/v/S31v/S31v_s1_c0_depth.mp4` | `takes/v/S31v/S31v_s1_c0_first.png` | `takes/v/S31v/S31v_s1_c0.mp4` | 28.1 | kept ([H] approved 2026-10-20) |
| S31v | 1 | 1 | 2681-2697 | `takes/v/S31v/S31v_s1_c1_depth.mp4` | `takes/v/S31v/S31v_s1_c1_first.png` | `takes/v/S31v/S31v_s1_c1.mp4` | 8.0 | kept ([H] approved 2026-10-20) |
| S31v | 2 | 0 | 2585-2681 | `takes/v/S31v/S31v_s2_c0_depth.mp4` | `takes/v/S31v/S31v_s2_c0_first.png` | `takes/v/S31v/S31v_s2_c0.mp4` | 29.1 | rejected (agent review: the other seed is the pick) |
| S31v | 2 | 1 | 2681-2697 | `takes/v/S31v/S31v_s2_c1_depth.mp4` | `takes/v/S31v/S31v_s2_c1_first.png` | `takes/v/S31v/S31v_s2_c1.mp4` | 7.0 | rejected (agent review: the other seed is the pick) |

## 2026-10-20T07:04:16-04:00 — V: shots (S09, S14, S29)

- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; template `comfy/api/video_ltx2_3_ic_lora.api.json`; 8 steps, euler_ancestral, cfg 1; 1280×704. Control: the Blender depth pass. First frame: the approved keyframe (clip 0) or the previous clip's last frame.
- **Prompts:** `config/v.json` (shot prompt + style); negative `NEGATIVE` in `scripts/ltx_v.py`. **Command:** `.venv/bin/python scripts/v_batch.py gen S09 S14 S29 --seeds 3,4`

| Shot | Seed | Clip | Plate frames | Control | First frame | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S09 | 3 | 0 | 572-668 | `takes/v/S09/S09_s3_c0_depth.mp4` | `takes/v/S09/S09_s3_c0_first.png` | `takes/v/S09/S09_s3_c0.mp4` | 28.2 | rejected (agent review: bunting slid off the sign onto the field edge) |
| S09 | 3 | 1 | 668-764 | `takes/v/S09/S09_s3_c1_depth.mp4` | `takes/v/S09/S09_s3_c1_first.png` | `takes/v/S09/S09_s3_c1.mp4` | 29.1 | rejected (agent review: bunting slid off the sign onto the field edge) |
| S09 | 3 | 2 | 764-772 | `takes/v/S09/S09_s3_c2_depth.mp4` | `takes/v/S09/S09_s3_c2_first.png` | `takes/v/S09/S09_s3_c2.mp4` | 6.0 | rejected (agent review: bunting slid off the sign onto the field edge) |
| S09 | 4 | 0 | 572-668 | `takes/v/S09/S09_s4_c0_depth.mp4` | `takes/v/S09/S09_s4_c0_first.png` | `takes/v/S09/S09_s4_c0.mp4` | 27.5 | rejected (agent review: a second tower appears mid-pan) |
| S09 | 4 | 1 | 668-764 | `takes/v/S09/S09_s4_c1_depth.mp4` | `takes/v/S09/S09_s4_c1_first.png` | `takes/v/S09/S09_s4_c1.mp4` | 29.1 | rejected (agent review: a second tower appears mid-pan) |
| S09 | 4 | 2 | 764-772 | `takes/v/S09/S09_s4_c2_depth.mp4` | `takes/v/S09/S09_s4_c2_first.png` | `takes/v/S09/S09_s4_c2.mp4` | 6.0 | rejected (agent review: a second tower appears mid-pan) |
| S14 | 3 | 0 | 993-1089 | `takes/v/S14/S14_s3_c0_depth.mp4` | `takes/v/S14/S14_s3_c0_first.png` | `takes/v/S14/S14_s3_c0.mp4` | 28.5 | kept ([H] approved 2026-10-20) |
| S14 | 3 | 1 | 1089-1145 | `takes/v/S14/S14_s3_c1_depth.mp4` | `takes/v/S14/S14_s3_c1_first.png` | `takes/v/S14/S14_s3_c1.mp4` | 18.0 | kept ([H] approved 2026-10-20) |
| S14 | 4 | 0 | 993-1089 | `takes/v/S14/S14_s4_c0_depth.mp4` | `takes/v/S14/S14_s4_c0_first.png` | `takes/v/S14/S14_s4_c0.mp4` | 34.1 | rejected (agent review: the other clean seed is the pick) |
| S14 | 4 | 1 | 1089-1145 | `takes/v/S14/S14_s4_c1_depth.mp4` | `takes/v/S14/S14_s4_c1_first.png` | `takes/v/S14/S14_s4_c1.mp4` | 19.3 | rejected (agent review: the other clean seed is the pick) |
| S29 | 3 | 0 | 2392-2488 | `takes/v/S29/S29_s3_c0_depth.mp4` | `takes/v/S29/S29_s3_c0_first.png` | `takes/v/S29/S29_s3_c0.mp4` | 30.5 | kept ([H] approved 2026-10-20) |
| S29 | 3 | 1 | 2488-2552 | `takes/v/S29/S29_s3_c1_depth.mp4` | `takes/v/S29/S29_s3_c1_first.png` | `takes/v/S29/S29_s3_c1.mp4` | 20.1 | kept ([H] approved 2026-10-20) |
| S29 | 4 | 0 | 2392-2488 | `takes/v/S29/S29_s4_c0_depth.mp4` | `takes/v/S29/S29_s4_c0_first.png` | `takes/v/S29/S29_s4_c0.mp4` | 28.4 | rejected (agent review: a red object appears in the raised hand) |
| S29 | 4 | 1 | 2488-2552 | `takes/v/S29/S29_s4_c1_depth.mp4` | `takes/v/S29/S29_s4_c1_first.png` | `takes/v/S29/S29_s4_c1.mp4` | 19.4 | rejected (agent review: a red object appears in the raised hand) |

## 2026-10-20T07:11:22-04:00 — S: keyframes (S09_end)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise from the layout per row (v3 and later; 1.0 = none); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S09_end`

| Shot | Seed | Denoise | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| S09_end_v8 | 2001 | 0.96 | renders/b/keyframe_end/S09/beauty/00772.png | `takes/keyframes/S09_end/S09_end_v8_s2001.png` | 92.4 | rejected (agent review: seed 2002 matches the layout's cranes better) |
| S09_end_v8 | 2002 | 0.96 | renders/b/keyframe_end/S09/beauty/00772.png | `takes/keyframes/S09_end/S09_end_v8_s2002.png` | 79.3 | kept (input to S09's reverse V run) |

## 2026-10-20T07:14:39-04:00 — V: shots (S09)

- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; template `comfy/api/video_ltx2_3_ic_lora.api.json`; 8 steps, euler_ancestral, cfg 1; 1280×704. Control: the Blender depth pass. First frame: the approved keyframe (clip 0) or the previous clip's last frame.
- **Prompts:** `config/v.json` (shot prompt + style); negative `NEGATIVE` in `scripts/ltx_v.py`. **Command:** `.venv/bin/python scripts/v_batch.py gen S09 --seeds 5,6`

| Shot | Seed | Clip | Plate frames | Control | First frame | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S09 | 5 | 0 | 572-668 | `takes/v/S09/S09_s5_c0_depth.mp4` | `takes/v/S09/S09_s5_c0_first.png` | `takes/v/S09/S09_s5_c0.mp4` | 40.4 | rejected (agent review: a dark band like a label on the tank) |
| S09 | 5 | 1 | 668-764 | `takes/v/S09/S09_s5_c1_depth.mp4` | `takes/v/S09/S09_s5_c1_first.png` | `takes/v/S09/S09_s5_c1.mp4` | 27.3 | rejected (agent review: a dark band like a label on the tank) |
| S09 | 5 | 2 | 764-772 | `takes/v/S09/S09_s5_c2_depth.mp4` | `takes/v/S09/S09_s5_c2_first.png` | `takes/v/S09/S09_s5_c2.mp4` | 6.0 | rejected (agent review: a dark band like a label on the tank) |
| S09 | 6 | 0 | 572-668 | `takes/v/S09/S09_s6_c0_depth.mp4` | `takes/v/S09/S09_s6_c0_first.png` | `takes/v/S09/S09_s6_c0.mp4` | 27.3 | kept ([H] approved 2026-10-20) |
| S09 | 6 | 1 | 668-764 | `takes/v/S09/S09_s6_c1_depth.mp4` | `takes/v/S09/S09_s6_c1_first.png` | `takes/v/S09/S09_s6_c1.mp4` | 27.5 | kept ([H] approved 2026-10-20) |
| S09 | 6 | 2 | 764-772 | `takes/v/S09/S09_s6_c2_depth.mp4` | `takes/v/S09/S09_s6_c2_first.png` | `takes/v/S09/S09_s6_c2.mp4` | 6.0 | kept ([H] approved 2026-10-20) |

**Agent review of the V batch (2026-10-20).** All 29 shots, seeds 1-2, then seeds 3-6 for three shots. Rejected at seeds 1-2: S09 (the bunting never stayed on the sign), S14 (leaves blew across the frame like embers), S29 (seed 2 grew a second hand; seed 1's V dropped to one finger), and single seeds of S16 (the plane bursts into a fireball), S18 (abrupt blackout and a hand), S22 (the point opens into a palm) and S28a (embers). Seeds 3-4 with revised prompts (`config/v.json`) fixed S14 and S29; S09 still lost the bunting. Seeds 5-6 generated S09 backwards from a new keyframe of the pan's last frame (`S09_end`, `config/v.json` "reverse"), so the sign and bunting are the take's anchor. Picks with flags: `config/v_picks.json`. Review pages: `.venv/bin/python scripts/v_review.py` → `takes/v/review_page<N>.png`. Status: pending [H].


## 2026-10-20T12:27:31-04:00 — S: keyframes (S12)

- **Model:** FLUX.2 [dev] `flux2_dev_fp8mixed.safetensors`, `mistral_3_small_flux2_fp4_mixed.safetensors`, `flux2-vae.safetensors`; 28 steps, euler, guidance 4.0, denoise from the layout per row (v3 and later; 1.0 = none); reference editing (ReferenceLatent, 1 MP per reference), 1920×1056.
- **Prompts:** `log/prompts/keyframes/<shot>.txt`. **Command:** `.venv/bin/python scripts/keyframes.py S12`

| Shot | Seed | Denoise | Inputs (reference 1 = layout) | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| S12_v8 | 2001 | 0.96 | renders/b/keyframe/S12/beauty/00880.png, takes/stills/kept/singer.png | `takes/keyframes/S12/S12_v8_s2001.png` | 135.5 | rejected (agent review: the other seed holds the layout) |
| S12_v8 | 2002 | 0.96 | renders/b/keyframe/S12/beauty/00880.png, takes/stills/kept/singer.png | `takes/keyframes/S12/S12_v8_s2002.png` | 110.2 | kept ([H] approved with its V take) |

## 2026-10-20T12:34:21-04:00 — V: shots (S12, S17, S19)

**Why (2026-10-20, [H] review of the V picks):** S12's walk was very unnatural and its corn was straight Blender; S17 was missing motion; S19's hand was off. Cause: the people's Blender stand-ins are rigid mannequins (`mannequin()` in `build_town.py`), and at full strength the depth guide held each take to them: S12's frozen mid-stride figure slid down the track, S17's grandmother stood still, and S19's hand followed the stand-in's blunt level cylinder arm (and the empty chair's profile in the depth didn't match the keyframe's chair, so it doubled). S12's corn came from its v7 keyframe (fixed as S06's: keyframe v8, real-corn wording, s2002). Fix: a per-shot depth guide strength, `"guide"` in `config/v.json` (LTXVAddGuide strength): S12 0.5, S19 0.5, S17 0.4. Test on S12 clip 0 (seed 1; scratchpad, not kept): 0.3, 0.5 and 0.7 all walked with alternating legs; at 0.3 he overtook the stand-in's path, so 0.5. Motion prompts rewritten (natural gait; grandma bends, lifts the pie out, turns; one index finger pointing). The old takes are in `takes/v/<shot>/rejected_h_review/`.

- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; template `comfy/api/video_ltx2_3_ic_lora.api.json`; 8 steps, euler_ancestral, cfg 1; 1280×704. Control: the Blender depth pass. First frame: the approved keyframe (clip 0) or the previous clip's last frame.
- **Prompts:** `config/v.json` (shot prompt + style); negative `NEGATIVE` in `scripts/ltx_v.py`. **Command:** `.venv/bin/python scripts/v_batch.py gen S12 S17 S19 --seeds 1,2`

| Shot | Seed | Clip | Plate frames | Control | First frame | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S12 | 1 | 0 | 880-976 | `takes/v/S12/S12_s1_c0_depth.mp4` | `takes/v/S12/S12_s1_c0_first.png` | `takes/v/S12/S12_s1_c0.mp4` | 29.4 | kept ([H] approved 2026-10-20) |
| S12 | 1 | 1 | 976-984 | `takes/v/S12/S12_s1_c1_depth.mp4` | `takes/v/S12/S12_s1_c1_first.png` | `takes/v/S12/S12_s1_c1.mp4` | 6.0 | kept ([H] approved 2026-10-20) |
| S12 | 2 | 0 | 880-976 | `takes/v/S12/S12_s2_c0_depth.mp4` | `takes/v/S12/S12_s2_c0_first.png` | `takes/v/S12/S12_s2_c0.mp4` | 29.5 | rejected (agent review: the other seed is the pick) |
| S12 | 2 | 1 | 976-984 | `takes/v/S12/S12_s2_c1_depth.mp4` | `takes/v/S12/S12_s2_c1_first.png` | `takes/v/S12/S12_s2_c1.mp4` | 6.0 | rejected (agent review: the other seed is the pick) |
| S17 | 1 | 0 | 1336-1432 | `takes/v/S17/S17_s1_c0_depth.mp4` | `takes/v/S17/S17_s1_c0_first.png` | `takes/v/S17/S17_s1_c0.mp4` | 30.1 | rejected ([H]: the take fades down, up and down again; each chained clip dimmed on its own); moved to `rejected_h_fade/` |
| S17 | 1 | 1 | 1432-1528 | `takes/v/S17/S17_s1_c1_depth.mp4` | `takes/v/S17/S17_s1_c1_first.png` | `takes/v/S17/S17_s1_c1.mp4` | 30.3 | rejected ([H]: the take fades down, up and down again; each chained clip dimmed on its own); moved to `rejected_h_fade/` |
| S17 | 1 | 2 | 1528-1560 | `takes/v/S17/S17_s1_c2_depth.mp4` | `takes/v/S17/S17_s1_c2_first.png` | `takes/v/S17/S17_s1_c2.mp4` | 11.0 | rejected ([H]: the take fades down, up and down again; each chained clip dimmed on its own); moved to `rejected_h_fade/` |
| S17 | 2 | 0 | 1336-1432 | `takes/v/S17/S17_s2_c0_depth.mp4` | `takes/v/S17/S17_s2_c0_first.png` | `takes/v/S17/S17_s2_c0.mp4` | 31.0 | rejected ([H]: the take fades down, up and down again; each chained clip dimmed on its own); moved to `rejected_h_fade/` |
| S17 | 2 | 1 | 1432-1528 | `takes/v/S17/S17_s2_c1_depth.mp4` | `takes/v/S17/S17_s2_c1_first.png` | `takes/v/S17/S17_s2_c1.mp4` | 30.0 | rejected ([H]: the take fades down, up and down again; each chained clip dimmed on its own); moved to `rejected_h_fade/` |
| S17 | 2 | 2 | 1528-1560 | `takes/v/S17/S17_s2_c2_depth.mp4` | `takes/v/S17/S17_s2_c2_first.png` | `takes/v/S17/S17_s2_c2.mp4` | 11.0 | rejected ([H]: the take fades down, up and down again; each chained clip dimmed on its own); moved to `rejected_h_fade/` |
| S19 | 1 | 0 | 1751-1831 | `takes/v/S19/S19_s1_c0_depth.mp4` | `takes/v/S19/S19_s1_c0_first.png` | `takes/v/S19/S19_s1_c0.mp4` | 25.0 | kept ([H] approved 2026-10-20) |
| S19 | 2 | 0 | 1751-1831 | `takes/v/S19/S19_s2_c0_depth.mp4` | `takes/v/S19/S19_s2_c0_first.png` | `takes/v/S19/S19_s2_c0.mp4` | 25.4 | rejected (agent review: the other seed is the pick) |

## 2026-10-20T12:42:00-04:00 — V: shots (S17)

**Why (2026-10-20, [H]: "S17 is fading in and out"):** the shot is three chained clips and each clip's prompt said the lights dim, so the take dimmed over frames 50-96, came back up by 117 and dimmed again over 148-193 (mean luma 90 → 28 → 79 → 25). The brief wants one dim, on "apple pie" (running gags: "Kitchen dims on 'apple pie'"). The prompt now holds the light steady (all three seeds measure 83-92 throughout), and the dim is a grade in E, timed to the second "pie!" (59.073 s, 3.40 s into the shot): black at 60% opacity faded in over 1 s, luma 90 → 44. Preview: `ffmpeg -i takes/v/S17/S17_s1.mp4 -f lavfi -i "color=black:s=1280x704:r=24:d=9.2" -filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.6,fade=in:st=3.4:d=1:alpha=1[k];[0:v][k]overlay=shortest=1,format=yuv420p" takes/v/S17/S17_s1_dim_preview.mp4`, with the master from 55.673 s in `takes/v/S17_dim_preview_with_audio.mp4`.

- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; template `comfy/api/video_ltx2_3_ic_lora.api.json`; 8 steps, euler_ancestral, cfg 1; 1280×704. Control: the Blender depth pass. First frame: the approved keyframe (clip 0) or the previous clip's last frame.
- **Prompts:** `config/v.json` (shot prompt + style); negative `NEGATIVE` in `scripts/ltx_v.py`. **Command:** `.venv/bin/python scripts/v_batch.py gen S17 --seeds 1,2,3`

| Shot | Seed | Clip | Plate frames | Control | First frame | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S17 | 1 | 0 | 1336-1432 | `takes/v/S17/S17_s1_c0_depth.mp4` | `takes/v/S17/S17_s1_c0_first.png` | `takes/v/S17/S17_s1_c0.mp4` | 29.3 | kept ([H] approved 2026-10-20) |
| S17 | 1 | 1 | 1432-1528 | `takes/v/S17/S17_s1_c1_depth.mp4` | `takes/v/S17/S17_s1_c1_first.png` | `takes/v/S17/S17_s1_c1.mp4` | 30.1 | kept ([H] approved 2026-10-20) |
| S17 | 1 | 2 | 1528-1560 | `takes/v/S17/S17_s1_c2_depth.mp4` | `takes/v/S17/S17_s1_c2_first.png` | `takes/v/S17/S17_s1_c2.mp4` | 11.0 | kept ([H] approved 2026-10-20) |
| S17 | 2 | 0 | 1336-1432 | `takes/v/S17/S17_s2_c0_depth.mp4` | `takes/v/S17/S17_s2_c0_first.png` | `takes/v/S17/S17_s2_c0.mp4` | 31.5 | rejected (agent review: a second pie appears on the table) |
| S17 | 2 | 1 | 1432-1528 | `takes/v/S17/S17_s2_c1_depth.mp4` | `takes/v/S17/S17_s2_c1_first.png` | `takes/v/S17/S17_s2_c1.mp4` | 30.3 | rejected (agent review: a second pie appears on the table) |
| S17 | 2 | 2 | 1528-1560 | `takes/v/S17/S17_s2_c2_depth.mp4` | `takes/v/S17/S17_s2_c2_first.png` | `takes/v/S17/S17_s2_c2.mp4` | 11.0 | rejected (agent review: a second pie appears on the table) |
| S17 | 3 | 0 | 1336-1432 | `takes/v/S17/S17_s3_c0_depth.mp4` | `takes/v/S17/S17_s3_c0_first.png` | `takes/v/S17/S17_s3_c0.mp4` | 32.0 | rejected (agent review: the pie goes back into the oven) |
| S17 | 3 | 1 | 1432-1528 | `takes/v/S17/S17_s3_c1_depth.mp4` | `takes/v/S17/S17_s3_c1_first.png` | `takes/v/S17/S17_s3_c1.mp4` | 31.0 | rejected (agent review: the pie goes back into the oven) |
| S17 | 3 | 2 | 1528-1560 | `takes/v/S17/S17_s3_c2_depth.mp4` | `takes/v/S17/S17_s3_c2_first.png` | `takes/v/S17/S17_s3_c2.mp4` | 11.0 | rejected (agent review: the pie goes back into the oven) |

**S17 dim removed (2026-10-20, [H]: "the dimming does not work in context. Remove it").** No grade on S17; the take `takes/v/S17/S17_s1.mp4` is used as generated, with steady light. The preview files were deleted.

## 2026-10-20T12:54:57-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 10.3 | test (method dropped: see the L note below) |

## 2026-10-20T12:55:14-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 8.0 | test (method dropped: see the L note below) |

## 2026-10-20T12:55:27-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 11.0 | test (method dropped: see the L note below) |

## 2026-10-20T12:56:31-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 13.3 | test (method dropped: see the L note below) |

## 2026-10-20T12:58:20-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 16.3 | test (method dropped: see the L note below) |

## 2026-10-20T12:59:23-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 31.1 | test (method dropped: see the L note below) |

## 2026-10-20T13:00:00-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 16.1 | test (method dropped: see the L note below) |

## 2026-10-20T13:00:43-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 8.0 | test (method dropped: see the L note below) |

## 2026-10-20T13:00:57-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 7.2 | test (method dropped: see the L note below) |

## 2026-10-20T13:01:22-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 9.1 | test (method dropped: see the L note below) |

## 2026-10-20T13:01:37-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 12.4 | test (method dropped: see the L note below) |

## 2026-10-20T13:02:09-04:00 — L: lip-sync (S22)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 10.0 | test (method dropped: see the L note below) |

## 2026-10-20T13:02:49-04:00 — L: lip-sync (S05, S12, S15, S19, S22, S26, S29, S29v)

- **Model:** LTX-2.3 22B distilled fp8 (`ltx-2.3-22b-distilled-fp8.safetensors`), audio-video; Gemma 3 12B fp4. Inpainting on the approved V take: the face mask is regenerated from the vocal stem, the audio held fixed; sigmas `0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`, euler, cfg 1; 1280×704 (S29v 704×1280).
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`, face boxes `takes/l/<shot>/faces.json` (`scripts/l_faces.py`). **Prompts:** `config/l.json` (the V prompt + "sing"). **Command:** `.venv/bin/python scripts/l_batch.py S05 S12 S15 S19 S22 S26 S29 S29v --seeds 1,2`

| Shot | Seed | Clip | Shot frames | Held | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S05 | 1 | 0 | 0-96 | 0 | `takes/l/S05/S05_s1_c0_in.mp4` | `takes/l/S05/S05_s1_c0_gen` | 34.1 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S05 | 1 | 1 | 88-104 | 9 | `takes/l/S05/S05_s1_c1_in.mp4` | `takes/l/S05/S05_s1_c1_gen` | 7.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S05 | 2 | 0 | 0-96 | 0 | `takes/l/S05/S05_s2_c0_in.mp4` | `takes/l/S05/S05_s2_c0_gen` | 31.1 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S05 | 2 | 1 | 88-104 | 9 | `takes/l/S05/S05_s2_c1_in.mp4` | `takes/l/S05/S05_s2_c1_gen` | 6.4 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S12 | 1 | 0 | 0-96 | 0 | `takes/l/S12/S12_s1_c0_in.mp4` | `takes/l/S12/S12_s1_c0_gen` | 33.2 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S12 | 1 | 1 | 88-104 | 9 | `takes/l/S12/S12_s1_c1_in.mp4` | `takes/l/S12/S12_s1_c1_gen` | 6.4 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S12 | 2 | 0 | 0-96 | 0 | `takes/l/S12/S12_s2_c0_in.mp4` | `takes/l/S12/S12_s2_c0_gen` | 31.1 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S12 | 2 | 1 | 88-104 | 9 | `takes/l/S12/S12_s2_c1_in.mp4` | `takes/l/S12/S12_s2_c1_gen` | 6.4 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S15 | 1 | 0 | 0-96 | 0 | `takes/l/S15/S15_s1_c0_in.mp4` | `takes/l/S15/S15_s1_c0_gen` | 33.1 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S15 | 1 | 1 | 88-168 | 9 | `takes/l/S15/S15_s1_c1_in.mp4` | `takes/l/S15/S15_s1_c1_gen` | 25.3 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S15 | 2 | 0 | 0-96 | 0 | `takes/l/S15/S15_s2_c0_in.mp4` | `takes/l/S15/S15_s2_c0_gen` | 30.2 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S15 | 2 | 1 | 88-168 | 9 | `takes/l/S15/S15_s2_c1_in.mp4` | `takes/l/S15/S15_s2_c1_gen` | 25.1 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S19 | 1 | 0 | 0-80 | 0 | `takes/l/S19/S19_s1_c0_in.mp4` | `takes/l/S19/S19_s1_c0_gen` | 27.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S19 | 2 | 0 | 0-80 | 0 | `takes/l/S19/S19_s2_c0_in.mp4` | `takes/l/S19/S19_s2_c0_gen` | 25.2 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S22 | 1 | 0 | 0-40 | 0 | `takes/l/S22/S22_s1_c0_in.mp4` | `takes/l/S22/S22_s1_c0_gen` | 15.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S22 | 2 | 0 | 0-40 | 0 | `takes/l/S22/S22_s2_c0_in.mp4` | `takes/l/S22/S22_s2_c0_gen` | 13.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S26 | 1 | 0 | 0-80 | 0 | `takes/l/S26/S26_s1_c0_in.mp4` | `takes/l/S26/S26_s1_c0_gen` | 28.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S26 | 2 | 0 | 0-80 | 0 | `takes/l/S26/S26_s2_c0_in.mp4` | `takes/l/S26/S26_s2_c0_gen` | 26.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S29 | 1 | 0 | 0-96 | 0 | `takes/l/S29/S29_s1_c0_in.mp4` | `takes/l/S29/S29_s1_c0_gen` | 33.3 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S29 | 1 | 1 | 88-160 | 9 | `takes/l/S29/S29_s1_c1_in.mp4` | `takes/l/S29/S29_s1_c1_gen` | 23.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S29 | 2 | 0 | 0-96 | 0 | `takes/l/S29/S29_s2_c0_in.mp4` | `takes/l/S29/S29_s2_c0_gen` | 33.3 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S29 | 2 | 1 | 88-160 | 9 | `takes/l/S29/S29_s2_c1_in.mp4` | `takes/l/S29/S29_s2_c1_gen` | 23.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S29v | 1 | 0 | 0-96 | 0 | `takes/l/S29v/S29v_s1_c0_in.mp4` | `takes/l/S29v/S29v_s1_c0_gen` | 32.1 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S29v | 1 | 1 | 88-160 | 9 | `takes/l/S29v/S29v_s1_c1_in.mp4` | `takes/l/S29v/S29v_s1_c1_gen` | 23.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S29v | 2 | 0 | 0-96 | 0 | `takes/l/S29v/S29v_s2_c0_in.mp4` | `takes/l/S29v/S29v_s2_c0_gen` | 31.3 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |
| S29v | 2 | 1 | 88-160 | 9 | `takes/l/S29v/S29v_s2_c1_in.mp4` | `takes/l/S29v/S29v_s2_c1_gen` | 23.0 | rejected (method dropped: synced on some seeds only; the head moved off the V body) |

## 2026-10-20T13:25:03-04:00 — L: lip-sync with LatentSync 1.6 (S22 --seeds 1)

- **Model:** LatentSync 1.6 (`ByteDance/LatentSync-1.6` `latentsync_unet.pt`, code `bytedance/LatentSync` a229c39), 20 steps, guidance 1.5, DeepCache.
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`; a face crop of 2.6 face heights from `takes/l/<shot>/faces.json` (`scripts/l_faces.py`), 512 px, 24 fps frames labelled 25 fps with the vocal sped up 25/24. Pasted back through a feathered ellipse around the face. **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Frames | Synced | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 36 | 38 | `takes/v/S22/S22_s2.mp4` | `takes/l/S22/S22_s1.mp4` | 59.5 | test (guidance 1.5) |

## 2026-10-20T13:26:31-04:00 — L: lip-sync with LatentSync 1.6 (S22 --seeds 1)

- **Model:** LatentSync 1.6 (`ByteDance/LatentSync-1.6` `latentsync_unet.pt`, code `bytedance/LatentSync` a229c39), 20 steps, guidance 2.5, DeepCache.
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`; a face crop of 2.6 face heights from `takes/l/<shot>/faces.json` (`scripts/l_faces.py`), 512 px, 24 fps frames labelled 25 fps with the vocal sped up 25/24. Pasted back through a feathered ellipse around the face. **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Frames | Synced | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 36 | 38 | `takes/v/S22/S22_s2.mp4` | `takes/l/S22/S22_s1.mp4` | 18.8 | test (guidance 2.5; chosen) |

## 2026-10-20T13:26:56-04:00 — L: lip-sync with LatentSync 1.6 (S22 --seeds 1)

- **Model:** LatentSync 1.6 (`ByteDance/LatentSync-1.6` `latentsync_unet.pt`, code `bytedance/LatentSync` a229c39), 20 steps, guidance 3.5, DeepCache.
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`; a face crop of 2.6 face heights from `takes/l/<shot>/faces.json` (`scripts/l_faces.py`), 512 px, 24 fps frames labelled 25 fps with the vocal sped up 25/24. Pasted back through a feathered ellipse around the face. **Command:** `.venv/bin/python scripts/l_batch.py S22 --seeds 1`

| Shot | Seed | Frames | Synced | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S22 | 1 | 36 | 38 | `takes/v/S22/S22_s2.mp4` | `takes/l/S22/S22_s1.mp4` | 18.9 | test (guidance 3.5) |

**L note (2026-10-20).** The L stage tried LTX-2.3's audio-video model on the approved V takes before LatentSync (the S22 runs above and the eight-shot batch; outputs in `takes/l/test/`, git-ignored). Regenerating only a face mask, with the vocal held fixed: the mouth kept the V grin at sigma 0.725, 0.909 and 1.0, with a louder vocal (loudnorm -16 LUFS), with a singing prompt, with dev + distilled LoRA, and with modality guidance 3 and 6. Re-denoising the whole frame (first frame held): 0.909 barely moved, 0.975 moved and drifted, 0.9875 with modality guidance 3 followed the words on S22. On all eight shots it synced on some seeds only, and the head moved off the V take's body (S12, S15, S29), so the pasted face missed. A plain IA2V control from S22's first frame did articulate, so the vocal itself was fine. Dropped for LatentSync 1.6 (`log/decisions.md`). LatentSync on S22: guidance 1.5 barely moved off the V grin, 2.5 followed the words, 3.5 smeared the lips pink. Alignment checked on S12 (moving camera): each crop frame matches LatentSync's output at offset 0; its 2 extra frames are end padding. Review: `takes/l/l_picks_reel.mp4` (horizontal picks with the master) and `takes/l/l_picks_vertical.mp4`.

## 2026-10-20T13:27:30-04:00 — L: lip-sync with LatentSync 1.6 (all L shots)

- **Model:** LatentSync 1.6 (`ByteDance/LatentSync-1.6` `latentsync_unet.pt`, code `bytedance/LatentSync` a229c39), 20 steps, guidance 2.5, DeepCache.
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`; a face crop of 2.6 face heights from `takes/l/<shot>/faces.json` (`scripts/l_faces.py`), 512 px, 24 fps frames labelled 25 fps with the vocal sped up 25/24. Pasted back through a feathered ellipse around the face. **Command:** `.venv/bin/python scripts/l_batch.py `

| Shot | Seed | Frames | Synced | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S05 | 1 | 100 | 102 | `takes/v/S05/S05_s1.mp4` | `takes/l/S05/S05_s1.mp4` | 35.2 | kept ([H] approved 2026-10-20) |
| S05 | 2 | 100 | 102 | `takes/v/S05/S05_s1.mp4` | `takes/l/S05/S05_s2.mp4` | 35.1 | rejected (agent review: seed 1 articulates more) |
| S12 | 1 | 100 | 102 | `takes/v/S12/S12_s1.mp4` | `takes/l/S12/S12_s1.mp4` | 35.1 | kept ([H] approved 2026-10-20) |
| S12 | 2 | 100 | 102 | `takes/v/S12/S12_s1.mp4` | `takes/l/S12/S12_s2.mp4` | 35.3 | rejected (agent review: seed 1 articulates more) |
| S15 | 1 | 165 | 167 | `takes/v/S15/S15_s1.mp4` | `takes/l/S15/S15_s1.mp4` | 51.5 | kept ([H] approved 2026-10-20) |
| S15 | 2 | 165 | 167 | `takes/v/S15/S15_s1.mp4` | `takes/l/S15/S15_s2.mp4` | 51.5 | rejected (agent review: seed 1 articulates more) |
| S19 | 1 | 78 | 80 | `takes/v/S19/S19_s1.mp4` | `takes/l/S19/S19_s1.mp4` | 29.5 | kept ([H] approved 2026-10-20) |
| S19 | 2 | 78 | 80 | `takes/v/S19/S19_s1.mp4` | `takes/l/S19/S19_s2.mp4` | 29.5 | rejected (agent review: seed 1 articulates more) |
| S22 | 1 | 36 | 38 | `takes/v/S22/S22_s2.mp4` | `takes/l/S22/S22_s1.mp4` | 19.1 | kept ([H] approved 2026-10-20) |
| S22 | 2 | 36 | 38 | `takes/v/S22/S22_s2.mp4` | `takes/l/S22/S22_s2.mp4` | 19.1 | rejected (agent review: seed 1 articulates more) |
| S26 | 1 | 78 | 80 | `takes/v/S26/S26_s1.mp4` | `takes/l/S26/S26_s1.mp4` | 29.3 | kept ([H] approved 2026-10-20) |
| S26 | 2 | 78 | 80 | `takes/v/S26/S26_s1.mp4` | `takes/l/S26/S26_s2.mp4` | 29.3 | rejected (agent review: seed 1 articulates more) |
| S29 | 1 | 161 | 163 | `takes/v/S29/S29_s3.mp4` | `takes/l/S29/S29_s1.mp4` | 50.6 | kept ([H] approved 2026-10-20) |
| S29 | 2 | 161 | 163 | `takes/v/S29/S29_s3.mp4` | `takes/l/S29/S29_s2.mp4` | 50.6 | rejected (agent review: seed 1 articulates more) |
| S29v | 1 | 161 | 163 | `takes/v/S29v/S29v_s2.mp4` | `takes/l/S29v/S29v_s1.mp4` | 51.0 | kept ([H] approved 2026-10-20) |
| S29v | 2 | 161 | 163 | `takes/v/S29v/S29v_s2.mp4` | `takes/l/S29v/S29v_s2.mp4` | 50.6 | rejected (agent review: seed 1 articulates more) |

## 2026-10-20T14:12:56-04:00 — G: generated pieces for the glitch passes (six_fingers_S29, six_fingers_S29v, wrong_smile_S32, server_racks)

- **Model:** FLUX.2 [dev] fp8 (`config/stills.json` model), img2img from a 1024 px crop (edits) or text-to-image (stills). **Prompts, boxes, frames:** `config/g.json`. **Command:** `.venv/bin/python scripts/g_assets.py `

| Asset | Frame | Seed | Denoise | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| six_fingers_S29 | 100 | 3001 | 0.8 | `takes/g/assets/six_fingers_S29/f100_s3001.png` | 53.8 | rejected (agent review: not six digits) |
| six_fingers_S29 | 100 | 3002 | 0.8 | `takes/g/assets/six_fingers_S29/f100_s3002.png` | 39.2 | rejected (agent review: not six digits) |
| six_fingers_S29 | 100 | 3003 | 0.8 | `takes/g/assets/six_fingers_S29/f100_s3003.png` | 39.1 | rejected (agent review: not six digits) |
| six_fingers_S29 | 118 | 3001 | 0.8 | `takes/g/assets/six_fingers_S29/f118_s3001.png` | 39.4 | rejected (agent review: not six digits) |
| six_fingers_S29 | 118 | 3002 | 0.8 | `takes/g/assets/six_fingers_S29/f118_s3002.png` | 39.2 | kept (agent pick; pending [H] with the G passes) |
| six_fingers_S29 | 118 | 3003 | 0.8 | `takes/g/assets/six_fingers_S29/f118_s3003.png` | 39.1 | rejected (agent review: not six digits) |
| six_fingers_S29 | 137 | 3001 | 0.8 | `takes/g/assets/six_fingers_S29/f137_s3001.png` | 39.3 | rejected (agent review: not six digits) |
| six_fingers_S29 | 137 | 3002 | 0.8 | `takes/g/assets/six_fingers_S29/f137_s3002.png` | 39.1 | rejected (agent review: not six digits) |
| six_fingers_S29 | 137 | 3003 | 0.8 | `takes/g/assets/six_fingers_S29/f137_s3003.png` | 39.1 | rejected (agent review: not six digits) |
| six_fingers_S29v | 95 | 3001 | 0.8 | `takes/g/assets/six_fingers_S29v/f95_s3001.png` | 41.4 | rejected (agent review: not six digits) |
| six_fingers_S29v | 95 | 3002 | 0.8 | `takes/g/assets/six_fingers_S29v/f95_s3002.png` | 39.2 | rejected (agent review: not six digits) |
| six_fingers_S29v | 95 | 3003 | 0.8 | `takes/g/assets/six_fingers_S29v/f95_s3003.png` | 39.2 | rejected (agent review: not six digits) |
| six_fingers_S29v | 102 | 3001 | 0.8 | `takes/g/assets/six_fingers_S29v/f102_s3001.png` | 40.0 | rejected (agent review: not six digits) |
| six_fingers_S29v | 102 | 3002 | 0.8 | `takes/g/assets/six_fingers_S29v/f102_s3002.png` | 39.2 | rejected (agent review: not six digits) |
| six_fingers_S29v | 102 | 3003 | 0.8 | `takes/g/assets/six_fingers_S29v/f102_s3003.png` | 39.2 | rejected (agent review: not six digits) |
| six_fingers_S29v | 109 | 3001 | 0.8 | `takes/g/assets/six_fingers_S29v/f109_s3001.png` | 40.1 | rejected (agent review: not six digits) |
| six_fingers_S29v | 109 | 3002 | 0.8 | `takes/g/assets/six_fingers_S29v/f109_s3002.png` | 39.2 | rejected (agent review: not six digits) |
| six_fingers_S29v | 109 | 3003 | 0.8 | `takes/g/assets/six_fingers_S29v/f109_s3003.png` | 39.3 | rejected (agent review: not six digits) |
| wrong_smile_S32 | 0 | 3001 | 0.6 | `takes/g/assets/wrong_smile_S32/f0_s3001.png` | 32.2 | rejected (agent review: another seed is the pick) |
| wrong_smile_S32 | 0 | 3002 | 0.6 | `takes/g/assets/wrong_smile_S32/f0_s3002.png` | 30.4 | rejected (agent review: another seed is the pick) |
| wrong_smile_S32 | 0 | 3003 | 0.6 | `takes/g/assets/wrong_smile_S32/f0_s3003.png` | 31.0 | kept (agent pick; pending [H] with the G passes) |
| server_racks | - | 3001 | - | `takes/g/assets/server_racks/server_racks_s3001.png` | 51.3 | rejected (agent review: another seed is the pick) |
| server_racks | - | 3002 | - | `takes/g/assets/server_racks/server_racks_s3002.png` | 50.1 | kept (agent pick; pending [H] with the G passes) |

## 2026-10-20T14:29:17-04:00 — G: generated pieces for the glitch passes (six_fingers_S29v)

- **Model:** FLUX.2 [dev] fp8 (`config/stills.json` model), img2img from a 1024 px crop (edits) or text-to-image (stills). **Prompts, boxes, frames:** `config/g.json`. **Command:** `.venv/bin/python scripts/g_assets.py six_fingers_S29v`

| Asset | Frame | Seed | Denoise | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| six_fingers_S29v | 102 | 3004 | 0.85 | `takes/g/assets/six_fingers_S29v/f102_s3004.png` | 44.1 | rejected (agent review: not six digits) |
| six_fingers_S29v | 102 | 3005 | 0.85 | `takes/g/assets/six_fingers_S29v/f102_s3005.png` | 43.1 | rejected (agent review: not six digits) |
| six_fingers_S29v | 102 | 3006 | 0.85 | `takes/g/assets/six_fingers_S29v/f102_s3006.png` | 43.1 | kept (agent pick; pending [H] with the G passes) |
| six_fingers_S29v | 102 | 3007 | 0.85 | `takes/g/assets/six_fingers_S29v/f102_s3007.png` | 43.1 | rejected (agent review: not six digits) |
| six_fingers_S29v | 102 | 3008 | 0.85 | `takes/g/assets/six_fingers_S29v/f102_s3008.png` | 43.1 | rejected (agent review: not six digits) |
| six_fingers_S29v | 102 | 3009 | 0.85 | `takes/g/assets/six_fingers_S29v/f102_s3009.png` | 43.1 | rejected (agent review: not six digits) |

## 2026-10-20T14:34:11-04:00 — G: glitch and decay passes (S29, S29v, S32)

- **Tool:** `scripts/g_pass.py` (Python, PIL, ffmpeg), cut to `timing/failure_map.json` (a frame is inside a region when frame / 24 falls in [start, end)). Settings and asset picks: `config/g.json`. **Command:** `.venv/bin/python scripts/g_pass.py S29 S29v S32`

| Shot | Frames | What | Output | superseded (re-run after review) |
| --- | --- | --- | --- | --- |
| S29 | 2392-2552 | six fingers on frames [100, 101, 118, 119, 137, 138], server racks on frame 127 | `takes/g/S29/S29_g.mp4` | superseded (re-run after review) |
| S29v | 2392-2552 | six fingers on frames [95, 96, 102, 103, 109, 110], server racks on frame 127 | `takes/g/S29v/S29v_g.mp4` | superseded (re-run after review) |
| S32 | 2691-3218 | S33 keyframe held, push-in to 1.6x; wrong smile on frames [328, 329, 330, 377, 378, 379, 426, 427, 428]; lossy decay on frames 518-527 | `takes/g/S32/S32_g.mp4` | superseded (re-run after review) |

## 2026-10-20T14:37:00-04:00 — G: glitch and decay passes (S29, S29v, S32)

- **Tool:** `scripts/g_pass.py` (Python, PIL, ffmpeg), cut to `timing/failure_map.json` (a frame is inside a region when frame / 24 falls in [start, end)). Settings and asset picks: `config/g.json`. **Command:** `.venv/bin/python scripts/g_pass.py S29 S29v S32`

| Shot | Frames | What | Output | candidate, pending [H] |
| --- | --- | --- | --- | --- |
| S29 | 2392-2552 | six fingers on frames [100, 101, 118, 119, 137, 138], server racks on frame 127 | `takes/g/S29/S29_g.mp4` | candidate, pending [H] |
| S29v | 2392-2552 | six fingers on frames [95, 96, 102, 103, 109, 110], server racks on frame 127 | `takes/g/S29v/S29v_g.mp4` | candidate, pending [H] |
| S32 | 2691-3218 | S33 keyframe held, push-in to 1.6x; wrong smile on frames [328, 329, 330, 377, 378, 379, 426, 427, 428]; lossy decay on frames 518-527 | `takes/g/S32/S32_g.mp4` | candidate, pending [H] |

## 2026-10-20T14:34:09-04:00 — G: S33 decay generations

- **Model:** LTX-2.3 22B distilled fp8, Gemma 3 12B fp4; video encoded and re-denoised at 0.45 (KSampler, 8 steps linear_quadratic, euler_ancestral, cfg 1, seed 3300+k), no control. Each generation starts from the one before, re-encoded at 50% size, x264 crf 36. Windows [[0, 97], [80, 97]], crossfaded over 17 frames.
- **Input:** gen0 = `takes/v/S33/S33_s1.mp4` with its clips' handles. **Prompt:** S33's V prompt + style (`config/v.json`). **Command:** `.venv/bin/python scripts/g_decay.py`

| Generation | Output | Seconds | Status |
| --- | --- | --- | --- |
| 1 | `takes/g/S33/gen1.mp4` | 72.5 | test (denoise 0.45: each generation became a new scene, with garbled lettering) |
| 2 | `takes/g/S33/gen2.mp4` | 56.2 | test (denoise 0.45: each generation became a new scene, with garbled lettering) |
| 3 | `takes/g/S33/gen3.mp4` | 53.2 | test (denoise 0.45: each generation became a new scene, with garbled lettering) |
| 4 | `takes/g/S33/gen4.mp4` | 63.4 | test (denoise 0.45: each generation became a new scene, with garbled lettering) |
| 5 | `takes/g/S33/gen5.mp4` | 53.1 | test (denoise 0.45: each generation became a new scene, with garbled lettering) |
| 6 | `takes/g/S33/gen6.mp4` | 53.1 | test (denoise 0.45: each generation became a new scene, with garbled lettering) |

## 2026-10-20T14:45:58-04:00 — G: S33 decay generations

- **Model:** LTX-2.3 22B distilled fp8, Gemma 3 12B fp4; video encoded and re-denoised at 0.15 (KSampler, 8 steps linear_quadratic, euler_ancestral, cfg 1, seed 3300+k), no control. Each generation starts from the one before, re-encoded at 50% size, x264 crf 36. Windows [[0, 97], [80, 97]], crossfaded over 17 frames.
- **Input:** gen0 = `takes/v/S33/S33_s1.mp4` with its clips' handles. **Prompt:** S33's V prompt + style (`config/v.json`). **Command:** `.venv/bin/python scripts/g_decay.py`

| Generation | Output | Seconds | Status |
| --- | --- | --- | --- |
| 1 | `takes/g/S33/gen1.mp4` | 49.1 | test (denoise 0.15: barely changes) |

## 2026-10-20T14:47:35-04:00 — G: S33 decay generations

- **Model:** LTX-2.3 22B distilled fp8, Gemma 3 12B fp4; video encoded and re-denoised at 0.25 (KSampler, 8 steps linear_quadratic, euler_ancestral, cfg 1, seed 3300+k), no control. Each generation starts from the one before, re-encoded at 50% size, x264 crf 36. Windows [[0, 97], [80, 97]], crossfaded over 17 frames.
- **Input:** gen0 = `takes/v/S33/S33_s1.mp4` with its clips' handles. **Prompt:** S33's V prompt + style (`config/v.json`). **Command:** `.venv/bin/python scripts/g_decay.py`

| Generation | Output | Seconds | Status |
| --- | --- | --- | --- |
| 1 | `takes/g/S33/gen1.mp4` | 52.1 | test (denoise 0.25: slight drift) |

## 2026-10-20T14:49:28-04:00 — G: S33 decay generations

- **Model:** LTX-2.3 22B distilled fp8, Gemma 3 12B fp4; video encoded and re-denoised at 0.32 (KSampler, 8 steps linear_quadratic, euler_ancestral, cfg 1, seed 3300+k), no control. Each generation starts from the one before, re-encoded at 50% size, x264 crf 36. Windows [[0, 97], [80, 97]], crossfaded over 17 frames.
- **Input:** gen0 = `takes/v/S33/S33_s1.mp4` with its clips' handles. **Prompt:** S33's V prompt + style (`config/v.json`). **Command:** `.venv/bin/python scripts/g_decay.py`

| Generation | Output | Seconds | Status |
| --- | --- | --- | --- |
| 1 | `takes/g/S33/gen1.mp4` | 49.3 | kept (denoise 0.32; pending [H] with the G passes) |
| 2 | `takes/g/S33/gen2.mp4` | 55.2 | kept (denoise 0.32; pending [H] with the G passes) |
| 3 | `takes/g/S33/gen3.mp4` | 50.2 | kept (denoise 0.32; pending [H] with the G passes) |
| 4 | `takes/g/S33/gen4.mp4` | 49.1 | kept (denoise 0.32; pending [H] with the G passes) |
| 5 | `takes/g/S33/gen5.mp4` | 59.5 | kept (denoise 0.32; pending [H] with the G passes) |
| 6 | `takes/g/S33/gen6.mp4` | 50.4 | kept (denoise 0.32; pending [H] with the G passes) |

## 2026-10-20T14:59:41-04:00 — G: glitch and decay passes (S33)

- **Tool:** `scripts/g_pass.py` (Python, PIL, ffmpeg), cut to `timing/failure_map.json` (a frame is inside a region when frame / 24 falls in [start, end)). Settings and asset picks: `config/g.json`. **Command:** `.venv/bin/python scripts/g_pass.py S33`

| Shot | Frames | What | Output | superseded (re-run after review) |
| --- | --- | --- | --- | --- |
| S33 | 3219-3388 | gen1-gen6 over F3 (frames 0-167), building from gen0 through the mask pass, the rest fades out over the last 24 | `takes/g/S33/S33_g.mp4` | superseded (re-run after review) |

## 2026-10-20T15:01:52-04:00 — G: glitch and decay passes (S33)

- **Tool:** `scripts/g_pass.py` (Python, PIL, ffmpeg), cut to `timing/failure_map.json` (a frame is inside a region when frame / 24 falls in [start, end)). Settings and asset picks: `config/g.json`. **Command:** `.venv/bin/python scripts/g_pass.py S33`

| Shot | Frames | What | Output | candidate, pending [H] |
| --- | --- | --- | --- | --- |
| S33 | 3219-3388 | gen1-gen6 over F3 (frames 0-167), building from gen0 through its measured mask, the rest fades out over the last 24 | `takes/g/S33/S33_g.mp4` | candidate, pending [H] |


**G note (2026-10-20).** The first S33 decay run (0.45) is in `takes/g/S33/test_045/`, the single-generation tests in `test_0.15/` and `test_0.25/`. S33's building mask was first the plate's mask pass; LTX drew the building shorter than the layout's, so the mask also kept sky, floodlights and corn tops, and the shot ended on the whole top-right corner. It is now a polygon measured on the take (static camera), minus the porch post. S34: `.venv/bin/python scripts/g_spectrogram.py` → `takes/g/S34/S34_spectrogram.png` (1920×1080; spectrogram of the no-fallback master, F1–F3 outlined, the no-fallback minus with-fallback level underneath). Review: `takes/g/g_reel.mp4` (S29, S32, S33, S34 with the master) and `takes/g/g_vertical.mp4`.

## 2026-10-20T16:10:11-04:00 — G: generated pieces for the glitch passes (recipe_card)

- **Model:** FLUX.2 [dev] fp8 (`config/stills.json` model), img2img from a 1024 px crop (edits) or text-to-image (stills). **Prompts, boxes, frames:** `config/g.json`. **Command:** `.venv/bin/python scripts/g_assets.py recipe_card`

| Asset | Frame | Seed | Denoise | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| recipe_card | - | 3101 | - | `takes/g/assets/recipe_card/recipe_card_s3101.png` | 69.4 | rejected (agent review: s3102 is the pick) |
| recipe_card | - | 3102 | - | `takes/g/assets/recipe_card/recipe_card_s3102.png` | 49.1 | kept (agent pick: the card large and centred) |
| recipe_card | - | 3103 | - | `takes/g/assets/recipe_card/recipe_card_s3103.png` | 50.1 | rejected (agent review: s3102 is the pick) |

## 2026-10-20T16:30:00-04:00 — O: overlays (surfaces, screen layer, cards)

- **Tool:** the Ghost in the Machine renderer pattern: `overlays/folks.html` + `overlays/folks.js` expose `renderFrame(t)`; `scripts/o_render.mjs` (Puppeteer 24.43.1, Chrome headless shell) screenshots frames to transparent PNGs. Fonts: Oswald, Lora, Caveat, Source Sans 3 (SIL OFL, `assets/fonts`). Data: `scripts/o_data.py` → `overlays/data/o_data.js` (lines and words from `timing/timing_map.json`, the F regions, the vocal stem's level per frame, the tracked surfaces, `config/o.json` texts).
- **Surfaces:** 35 (mugs S05/S18/S26/S31/S31v; S08's 12 yard signs; S09 FUTURE SITE OF; the S14 and S28a marquees; S18's bill ticking up; S19's tag, TBD, and S25's ALSO TBD; S28b's gauge; the S15 and S16 sky letters; S20's nine TV quads for E; S17's recipe card). Placed by hand on a frame of each approved take and tracked with `scripts/o_track.py` (OpenCV LK + similarity/affine fits, ComfyUI's venv); S18's bill keyframed at frames 0, 97 and 194. Tracks and review sheets: `takes/o/tracks/`.
- **Screen layer:** the label throughout; karaoke captions (sung words white, the rest dimmed); the four caption swaps on the half beat (0.36 s at 83.35 bpm); S29's captions jittering with the vocal level inside F1 only; S32's letters jittering and smearing inside F2 only; each sung "artificial intelligence" in S32 at 1.0, 1.4, 1.9 times the size; S32's fine print scrolling at 760 px/s; the S05 and S24 lower thirds; the S20 counters ($55,700,000, 95 ads, data centers mentioned: 0).
- **Cards:** title (S02), S34's card, the fact card (S36) with the label, and the vertical cut's two-second label card.
- **S17 insert still:** FLUX.2, `config/g.json` `recipe_card`, seed 3102 (a blank card; O writes it).
- **Command:** `scripts/o_render_all.sh 6` (1 min). **Outputs:** `takes/o/surface/<shot>/`, `takes/o/screen/` (song frames 0–3388), `screen_nojitter/` and `screen_portrait/` (S29–S31), `cards/` (git-ignored, regenerable).
- **Status:** candidate, pending [H] at the rough cut.

## 2026-10-20T16:16:46-04:00 — L: lip-sync with LatentSync 1.6 (S10 S21 S30 S30v --seeds 1,2)

- **Model:** LatentSync 1.6 (`ByteDance/LatentSync-1.6` `latentsync_unet.pt`, code `bytedance/LatentSync` a229c39), 20 steps, guidance 2.5, DeepCache.
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`; a face crop of 2.6 face heights from `takes/l/<shot>/faces.json` (`scripts/l_faces.py`), 512 px, 24 fps frames labelled 25 fps with the vocal sped up 25/24. Pasted back through a feathered ellipse around the face. **Command:** `.venv/bin/python scripts/l_batch.py S10 S21 S30 S30v --seeds 1,2`

| Shot | Seed | Frames | Synced | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S10 | 1 | 60 | 62 | `takes/l/S10/source.mp4` | `takes/l/S10/S10_s1.mp4` | 27.3 | candidate (pick), pending [H] at the rough cut |
| S10 | 2 | 60 | 62 | `takes/l/S10/source.mp4` | `takes/l/S10/S10_s2.mp4` | 24.9 | rejected (agent review: seed 1 is the pick) |
| S21 | 1 | 65 | 67 | `takes/l/S21/source.mp4` | `takes/l/S21/S21_s1.mp4` | 26.6 | candidate (pick), pending [H] at the rough cut |
| S21 | 2 | 65 | 67 | `takes/l/S21/source.mp4` | `takes/l/S21/S21_s2.mp4` | 26.5 | rejected (agent review: seed 1 is the pick) |
| S30 | 1 | 32 | 34 | `takes/l/S30/source.mp4` | `takes/l/S30/S30_s1.mp4` | 18.1 | candidate (pick), pending [H] at the rough cut |
| S30 | 2 | 32 | 34 | `takes/l/S30/source.mp4` | `takes/l/S30/S30_s2.mp4` | 18.2 | rejected (agent review: seed 1 is the pick) |
| S30v | 1 | 32 | 34 | `takes/l/S30v/source.mp4` | `takes/l/S30v/S30v_s1.mp4` | 18.0 | candidate (pick), pending [H] at the rough cut |
| S30v | 2 | 32 | 34 | `takes/l/S30v/source.mp4` | `takes/l/S30v/S30v_s2.mp4` | 18.1 | rejected (agent review: seed 1 is the pick) |

## 2026-10-20T16:21:24-04:00 — L: lip-sync with LatentSync 1.6 (S30 S30v --seeds 1,2)

- **Model:** LatentSync 1.6 (`ByteDance/LatentSync-1.6` `latentsync_unet.pt`, code `bytedance/LatentSync` a229c39), 20 steps, guidance 2.5, DeepCache.
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`; a face crop of 2.6 face heights from `takes/l/<shot>/faces.json` (`scripts/l_faces.py`), 512 px, 24 fps frames labelled 25 fps with the vocal sped up 25/24. Pasted back through a feathered ellipse around the face. **Command:** `.venv/bin/python scripts/l_batch.py S30 S30v --seeds 1,2`

| Shot | Seed | Frames | Synced | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S30 | 1 | 32 | 34 | `takes/l/S30/source.mp4` | `takes/l/S30/S30_s1.mp4` | 18.2 | candidate (pick), pending [H] at the rough cut |
| S30 | 2 | 32 | 34 | `takes/l/S30/source.mp4` | `takes/l/S30/S30_s2.mp4` | 18.1 | rejected (agent review: seed 1 is the pick) |
| S30v | 1 | 32 | 34 | `takes/l/S30v/source.mp4` | `takes/l/S30v/S30v_s1.mp4` | 18.2 | candidate (pick), pending [H] at the rough cut |
| S30v | 2 | 32 | 34 | `takes/l/S30v/source.mp4` | `takes/l/S30v/S30v_s2.mp4` | 18.0 | rejected (agent review: seed 1 is the pick) |

## 2026-10-20T16:24:07-04:00 — G: generated pieces for the glitch passes (tv_tractor, tv_ballgame)

- **Model:** FLUX.2 [dev] fp8 (`config/stills.json` model), img2img from a 1024 px crop (edits) or text-to-image (stills). **Prompts, boxes, frames:** `config/g.json`. **Command:** `.venv/bin/python scripts/g_assets.py tv_tractor tv_ballgame`

| Asset | Frame | Seed | Denoise | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- |
| tv_tractor | - | 3201 | - | `takes/g/assets/tv_tractor/tv_tractor_s3201.png` | 65.9 | kept (agent pick) |
| tv_tractor | - | 3202 | - | `takes/g/assets/tv_tractor/tv_tractor_s3202.png` | 46.1 | rejected (agent review: the other seed is the pick) |
| tv_ballgame | - | 3201 | - | `takes/g/assets/tv_ballgame/tv_ballgame_s3201.png` | 49.1 | rejected (agent review: the other seed is the pick) |
| tv_ballgame | - | 3202 | - | `takes/g/assets/tv_ballgame/tv_ballgame_s3202.png` | 46.1 | kept (agent pick) |

**S30 note (2026-10-20).** The first S30/S30v runs synced the held frame to the tail of the held "sky—" (105.75 s), which barely moved the mouth; they are in `takes/l/test/s30_sky/` and rejected. The kept runs sync it to the next line from 107.713 s, so over the ST4 gap he silently mouths the words he is about to sing.

## 2026-10-20T16:40:00-04:00 — E: rough cut (main and vertical)

- **Tool:** `scripts/e_edit.py` (numpy/PIL compositing, ffmpeg libx264 crf 14 per segment, concat, AAC 256k), cut list `config/edit.json`. Every frame: the shot's approved picture on the 1920×1056 stage (takes ×1.5), O's surface layer by multiply (screen for the sky letters), S20/S23's TV wall (content warped into the tracked screen quads, keyed to the screens' dark pixels), filled to 1920×1080, the grade (halation 0.1 over luma 0.72, grain 0.012, the same on every shot), then O's screen layer.
- **Structure:** S01 cold open (song frames 2392–2629 on the with-fallback master, no G pass, captions without the F1 jitter), then the song from 0 s; S02 title (frames 0–83) and S03 (84–155, placeholder) inside the intro, then S04; S07 the approved Granddad photo with a 10% push-in; S10 the lip-synced S05 porch, frozen from its frame 34 (mid "data—") to the "—day." cut; S17's recipe-card insert (song frames 1440–1499, in the gap between the two "apple pie"s); S20's TVs (two FLUX.2 stills with the approved singer sheet: `tv_tractor` s3201, `tv_ballgame` s3202, the tractor's hood lettering blurred; the rest approved takes) and S23 every screen on S05; S24 S05's frames with the Too PAC lower third; S25 S19's frames with ALSO TBD; S21 and S30 their L takes (S30's LED blinks red at 2.5 Hz); S27–S28 the montage parts; S29, S32, S33 the G passes; after the song S34 (plot 4 s, card 4 s), S35 (8 s, placeholder), S36 (fact card 12 s). Audio: the cold open's with-fallback span with a 0.25 s fade, the no-fallback master, and a synthetic hum (60/120/180 Hz plus filtered noise, −24 dB) from 136 s through the bookends.
- **Vertical:** S29v (G), S30v (L), S31v with the mug; the portrait screen layer; a two-second label card; 1080×1920.
- **Command:** `.venv/bin/python scripts/e_edit.py all --jobs 8` (3 min 50 s). **Outputs (git-ignored):** `takes/e/folks_like_us_main.mp4` (4299 frames, 179.1 s), `takes/e/folks_like_us_vertical.mp4` (347 frames, 14.5 s); review copies `takes/e/rough_cut_review.mp4` (720p) and `rough_cut_vertical_review.mp4`.
- **Status:** rough cut, pending [H] (brief checkpoint: the four stop gags land over the vocal gaps, the G passes sit inside F1–F3 only). S03 and S35 wait for [H]'s screen captures.

**Vertical fix (2026-10-20, [H]: "the vertical render appears corrupt").** `finish()` filled every picture to the main cut's 1920×1080, and the vertical encoder read those bytes as 1080×1920 (same byte count, so nothing failed): every song frame came out as horizontal streaks; only the label card, a full-frame card, was right. `finish()` now takes the output size, and both renderers assert each frame's size before writing it. Re-rendered: `.venv/bin/python scripts/e_edit.py vertical`.

## 2026-10-20T20:53:42-04:00 — V: shots (S16, S13, S28a, S28b, S27a, S27b, S27c, S27d, S27e)

- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; template `comfy/api/video_ltx2_3_ic_lora.api.json`; 8 steps, euler_ancestral, cfg 1; 1280×704. Control: the Blender depth pass. First frame: the approved keyframe (clip 0) or the previous clip's last frame.
- **Prompts:** `config/v.json` (shot prompt + style); negative `NEGATIVE` in `scripts/ltx_v.py`. **Command:** `.venv/bin/python scripts/v_batch.py gen S16 S13 S28a S28b S27a S27b S27c S27d S27e --seeds 11,12`

| Shot | Seed | Clip | Plate frames | Control | First frame | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S16 | 11 | 0 | 1308-1372 | `takes/v/S16/S16_s11_c0_depth.mp4` | `takes/v/S16/S16_s11_c0_first.png` | `takes/v/S16/S16_s11_c0.mp4` | 32.2 | pending [H] |
| S16 | 12 | 0 | 1308-1372 | `takes/v/S16/S16_s12_c0_depth.mp4` | `takes/v/S16/S16_s12_c0_first.png` | `takes/v/S16/S16_s12_c0.mp4` | 23.5 | pending [H] |
| S13 | 11 | 0 | 980-1036 | `takes/v/S13/S13_s11_c0_depth.mp4` | `takes/v/S13/S13_s11_c0_first.png` | `takes/v/S13/S13_s11_c0.mp4` | 18.1 | pending [H] |
| S13 | 12 | 0 | 980-1036 | `takes/v/S13/S13_s12_c0_depth.mp4` | `takes/v/S13/S13_s12_c0_first.png` | `takes/v/S13/S13_s12_c0.mp4` | 15.4 | pending [H] |
| S28a | 11 | 0 | 2390-2414 | `takes/v/S28a/S28a_s11_c0_depth.mp4` | `takes/v/S28a/S28a_s11_c0_first.png` | `takes/v/S28a/S28a_s11_c0.mp4` | 8.0 | pending [H] |
| S28a | 12 | 0 | 2390-2414 | `takes/v/S28a/S28a_s12_c0_depth.mp4` | `takes/v/S28a/S28a_s12_c0_first.png` | `takes/v/S28a/S28a_s12_c0.mp4` | 8.4 | pending [H] |
| S28b | 11 | 0 | 2408-2424 | `takes/v/S28b/S28b_s11_c0_depth.mp4` | `takes/v/S28b/S28b_s11_c0_first.png` | `takes/v/S28b/S28b_s11_c0.mp4` | 7.0 | pending [H] |
| S28b | 12 | 0 | 2408-2424 | `takes/v/S28b/S28b_s12_c0_depth.mp4` | `takes/v/S28b/S28b_s12_c0_first.png` | `takes/v/S28b/S28b_s12_c0.mp4` | 6.3 | pending [H] |
| S27a | 11 | 0 | 2320-2336 | `takes/v/S27a/S27a_s11_c0_depth.mp4` | `takes/v/S27a/S27a_s11_c0_first.png` | `takes/v/S27a/S27a_s11_c0.mp4` | 7.0 | pending [H] |
| S27a | 12 | 0 | 2320-2336 | `takes/v/S27a/S27a_s12_c0_depth.mp4` | `takes/v/S27a/S27a_s12_c0_first.png` | `takes/v/S27a/S27a_s12_c0.mp4` | 7.0 | pending [H] |
| S27b | 11 | 0 | 2334-2350 | `takes/v/S27b/S27b_s11_c0_depth.mp4` | `takes/v/S27b/S27b_s11_c0_first.png` | `takes/v/S27b/S27b_s11_c0.mp4` | 6.0 | pending [H] |
| S27b | 12 | 0 | 2334-2350 | `takes/v/S27b/S27b_s12_c0_depth.mp4` | `takes/v/S27b/S27b_s12_c0_first.png` | `takes/v/S27b/S27b_s12_c0.mp4` | 7.0 | pending [H] |
| S27c | 11 | 0 | 2348-2364 | `takes/v/S27c/S27c_s11_c0_depth.mp4` | `takes/v/S27c/S27c_s11_c0_first.png` | `takes/v/S27c/S27c_s11_c0.mp4` | 7.0 | pending [H] |
| S27c | 12 | 0 | 2348-2364 | `takes/v/S27c/S27c_s12_c0_depth.mp4` | `takes/v/S27c/S27c_s12_c0_first.png` | `takes/v/S27c/S27c_s12_c0.mp4` | 7.0 | pending [H] |
| S27d | 11 | 0 | 2362-2378 | `takes/v/S27d/S27d_s11_c0_depth.mp4` | `takes/v/S27d/S27d_s11_c0_first.png` | `takes/v/S27d/S27d_s11_c0.mp4` | 7.0 | pending [H] |
| S27d | 12 | 0 | 2362-2378 | `takes/v/S27d/S27d_s12_c0_depth.mp4` | `takes/v/S27d/S27d_s12_c0_first.png` | `takes/v/S27d/S27d_s12_c0.mp4` | 7.0 | pending [H] |
| S27e | 11 | 0 | 2376-2392 | `takes/v/S27e/S27e_s11_c0_depth.mp4` | `takes/v/S27e/S27e_s11_c0_first.png` | `takes/v/S27e/S27e_s11_c0.mp4` | 7.0 | pending [H] |
| S27e | 12 | 0 | 2376-2392 | `takes/v/S27e/S27e_s12_c0_depth.mp4` | `takes/v/S27e/S27e_s12_c0_first.png` | `takes/v/S27e/S27e_s12_c0.mp4` | 7.0 | pending [H] |

## 2026-10-20T20:58:10-04:00 — L: lip-sync with LatentSync 1.6 (S19c --seeds 1)

- **Model:** LatentSync 1.6 (`ByteDance/LatentSync-1.6` `latentsync_unet.pt`, code `bytedance/LatentSync` a229c39), 20 steps, guidance 2.5, DeepCache.
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`; a face crop of 2.6 face heights from `takes/l/<shot>/faces.json` (`scripts/l_faces.py`), 512 px, 24 fps frames labelled 25 fps with the vocal sped up 25/24. Pasted back through a feathered ellipse around the face. **Command:** `.venv/bin/python scripts/l_batch.py S19c --seeds 1`

| Shot | Seed | Frames | Synced | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S19c | 1 | 74 | 76 | `takes/l/S19c/source.mp4` | `takes/l/S19c/S19c_s1.mp4` | 31.2 | pending [H] |

## 2026-10-20T20:50-04:00 — B: plates for the lengthened shots (S13, S16, S27a–e, S28a–b)

- **Command:** `.venv/bin/python scripts/v_batch.py plates S13 S16 S27a S27b S27c S27d S27e S28a S28b --jobs 5` (1 min). Spans from `config/shots_b.json` "span" (the [H] rough-cut notes). **Outputs (git-ignored):** `renders/b/v_plates/<shot>/`. Kept.

## 2026-10-20T21:00-04:00 — O, E: rough cut 2 (the [H] rough-cut notes)

- **Picks:** V S13 s11, S16 s12, S27a–e s11, S28a s11, S28b s11 (`config/v_picks.json`); L S19c s1. All pending [H].
- **O:** `~/ComfyUI/.venv/bin/python scripts/o_track.py S16 S28a S28b`, then those surfaces re-rendered. New cards `s34_over`, `vote`, `vote_portrait`; `fact` and `labelcard` re-rendered with the new credits line (`scripts/o_render_all.sh` lists them all).
- **E:** `.venv/bin/python scripts/e_edit.py all --jobs 8` (3 min 50 s). Outputs (git-ignored):
  - `takes/e/folks_like_us_main.mp4`: 4419 frames, 184.1 s.
  - `takes/e/folks_like_us_vertical.mp4`: 443 frames, 18.5 s.
  - Review copies at 720p and 540×960.
- **Status:** rough cut 2, pending [H]. S03 and S35 are still placeholders.

## 2026-10-20T21:30-04:00 — E, O: TV wall person masks; credit line (rough cut 2, revised)

- **E people:** `~/ComfyUI/.venv/bin/python scripts/e_people.py`.
  - Model: torchvision 0.29.1 `maskrcnn_resnet50_fpn_v2`, COCO_V1 weights (`maskrcnn_resnet50_fpn_v2_coco-73cbd019.pth`, sha256 73cbd019…).
  - Score ≥ 0.5, 156 frames, 13 s.
  - Output: `takes/e/people/S20/` (git-ignored).
- **O:** the `fact` and `labelcard` cards re-rendered (`scripts/o_render_all.sh` entries).
- **E:** `.venv/bin/python scripts/e_edit.py all --jobs 8 --only 20_song_01829 23_song_02086 41_S36`, then reassembled. The main cut is 4419 frames (184.1 s) and the vertical 443 frames (18.5 s); review copies were rebuilt.
- **Status:** rough cut 2, pending [H].

## 2026-10-20T21:45-04:00 — O, E: S15 "A I" moved off the label

- **O:** the S15 sky_ai quad was moved in `config/o.json`. Commands: `~/ComfyUI/.venv/bin/python scripts/o_track.py S15`, then the S15 surface layer was re-rendered (165 frames).
- **E:** `.venv/bin/python scripts/e_edit.py main --jobs 4 --only 14_song_01143`, then reassembled; the review copy was rebuilt.
- **Status:** rough cut 2, pending [H].

## 2026-10-20T21:58:26-04:00 — L: lip-sync with LatentSync 1.6 (S26x --seeds 1)

- **Model:** LatentSync 1.6 (`ByteDance/LatentSync-1.6` `latentsync_unet.pt`, code `bytedance/LatentSync` a229c39), 20 steps, guidance 2.5, DeepCache.
- **Inputs:** the V pick (`config/v_picks.json`), `audio/stems/Folks Like Us (Vocals).wav`; a face crop of 2.6 face heights from `takes/l/<shot>/faces.json` (`scripts/l_faces.py`), 512 px, 24 fps frames labelled 25 fps with the vocal sped up 25/24. Pasted back through a feathered ellipse around the face. **Command:** `.venv/bin/python scripts/l_batch.py S26x --seeds 1`

| Shot | Seed | Frames | Synced | Input | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S26x | 1 | 78 | 80 | `takes/l/S26x/source.mp4` | `takes/l/S26x/S26x_s1.mp4` | 29.7 | pending [H] |

## 2026-10-20T22:00-04:00 — L, O, E: S25 cut, S26 re-synced earlier, montage lengthened

- **L:** S26x (S26's V take, synced to 2228–2306).
  - Commands: `.venv/bin/python scripts/l_batch.py S26x --prepare`, `~/ComfyUI/.venv/bin/python scripts/l_faces.py S26x`, `.venv/bin/python scripts/l_batch.py S26x --seeds 1`.
  - Output: `takes/l/S26x/S26x_s1.mp4`, pending [H] (its row is in the L table appended above).
- **V picks:** S27a–e, S28a and S28b now point at the untrimmed clips `<part>_s11_c0.mp4`.
- **O:** `~/ComfyUI/.venv/bin/python scripts/o_track.py S28a S28b`, then the S28a and S28b surfaces re-rendered.
- **E:** `.venv/bin/python scripts/e_edit.py main --jobs 8` produced the main cut, 4419 frames (184.1 s), plus a rebuilt review copy. The vertical cut is unchanged.
- **Status:** rough cut 2, pending [H].

## 2026-10-20T22:09:46-04:00 — V: shots (S27a, S27b, S27c, S27d, S27e, S28a, S28b)

- **Model:** LTX-2.3 22B distilled fp8 + IC-LoRA union control (ref0.5), Gemma 3 12B fp4; template `comfy/api/video_ltx2_3_ic_lora.api.json`; 8 steps, euler_ancestral, cfg 1; 1280×704. Control: the Blender depth pass. First frame: the approved keyframe (clip 0) or the previous clip's last frame.
- **Prompts:** `config/v.json` (shot prompt + style); negative `NEGATIVE` in `scripts/ltx_v.py`. **Command:** `.venv/bin/python scripts/v_batch.py gen S27a S27b S27c S27d S27e S28a S28b --seeds 21,22`

| Shot | Seed | Clip | Plate frames | Control | First frame | Output | Seconds | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S27a | 21 | 0 | 2293-2317 | `takes/v/S27a/S27a_s21_c0_depth.mp4` | `takes/v/S27a/S27a_s21_c0_first.png` | `takes/v/S27a/S27a_s21_c0.mp4` | 40.6 | pending [H] |
| S27a | 22 | 0 | 2293-2317 | `takes/v/S27a/S27a_s22_c0_depth.mp4` | `takes/v/S27a/S27a_s22_c0_first.png` | `takes/v/S27a/S27a_s22_c0.mp4` | 9.3 | pending [H] |
| S27b | 21 | 0 | 2316-2340 | `takes/v/S27b/S27b_s21_c0_depth.mp4` | `takes/v/S27b/S27b_s21_c0_first.png` | `takes/v/S27b/S27b_s21_c0.mp4` | 9.0 | pending [H] |
| S27b | 22 | 0 | 2316-2340 | `takes/v/S27b/S27b_s22_c0_depth.mp4` | `takes/v/S27b/S27b_s22_c0_first.png` | `takes/v/S27b/S27b_s22_c0.mp4` | 9.0 | pending [H] |
| S27c | 21 | 0 | 2339-2363 | `takes/v/S27c/S27c_s21_c0_depth.mp4` | `takes/v/S27c/S27c_s21_c0_first.png` | `takes/v/S27c/S27c_s21_c0.mp4` | 8.0 | pending [H] |
| S27c | 22 | 0 | 2339-2363 | `takes/v/S27c/S27c_s22_c0_depth.mp4` | `takes/v/S27c/S27c_s22_c0_first.png` | `takes/v/S27c/S27c_s22_c0.mp4` | 9.0 | pending [H] |
| S27d | 21 | 0 | 2362-2386 | `takes/v/S27d/S27d_s21_c0_depth.mp4` | `takes/v/S27d/S27d_s21_c0_first.png` | `takes/v/S27d/S27d_s21_c0.mp4` | 8.0 | pending [H] |
| S27d | 22 | 0 | 2362-2386 | `takes/v/S27d/S27d_s22_c0_depth.mp4` | `takes/v/S27d/S27d_s22_c0_first.png` | `takes/v/S27d/S27d_s22_c0.mp4` | 9.0 | pending [H] |
| S27e | 21 | 0 | 2385-2409 | `takes/v/S27e/S27e_s21_c0_depth.mp4` | `takes/v/S27e/S27e_s21_c0_first.png` | `takes/v/S27e/S27e_s21_c0.mp4` | 9.0 | pending [H] |
| S27e | 22 | 0 | 2385-2409 | `takes/v/S27e/S27e_s22_c0_depth.mp4` | `takes/v/S27e/S27e_s22_c0_first.png` | `takes/v/S27e/S27e_s22_c0.mp4` | 8.0 | pending [H] |
| S28a | 21 | 0 | 2408-2432 | `takes/v/S28a/S28a_s21_c0_depth.mp4` | `takes/v/S28a/S28a_s21_c0_first.png` | `takes/v/S28a/S28a_s21_c0.mp4` | 9.3 | pending [H] |
| S28a | 22 | 0 | 2408-2432 | `takes/v/S28a/S28a_s22_c0_depth.mp4` | `takes/v/S28a/S28a_s22_c0_first.png` | `takes/v/S28a/S28a_s22_c0.mp4` | 8.0 | pending [H] |
| S28b | 21 | 0 | 2433-2457 | `takes/v/S28b/S28b_s21_c0_depth.mp4` | `takes/v/S28b/S28b_s21_c0_first.png` | `takes/v/S28b/S28b_s21_c0.mp4` | 9.0 | pending [H] |
| S28b | 22 | 0 | 2433-2457 | `takes/v/S28b/S28b_s22_c0_depth.mp4` | `takes/v/S28b/S28b_s22_c0_first.png` | `takes/v/S28b/S28b_s22_c0.mp4` | 8.0 | pending [H] |

## 2026-10-20T22:30-04:00 — B, V, O, E: montage from "something" to "and"

- **B:** `.venv/bin/python scripts/v_batch.py plates S27a S27b S27c S27d S27e S28a S28b --jobs 7` (45 s). Spans come from `config/shots_b.json`.
- **V:** `.venv/bin/python scripts/v_batch.py gen S27a S27b S27c S27d S27e S28a S28b --seeds 21,22`. Its rows are in the V table appended above. Picks are seed 21, pending [H].
- **O:** `~/ComfyUI/.venv/bin/python scripts/o_track.py S28a S28b`, then those surfaces re-rendered.
- **E:** `.venv/bin/python scripts/e_edit.py main --jobs 8` produced the main cut, 4419 frames (184.1 s), plus a rebuilt review copy. The vertical cut is unchanged.
- **Status:** rough cut 2, pending [H].

## 2026-10-20T22:28:34-04:00 — G: glitch and decay passes (S33)

- **Tool:** `scripts/g_pass.py` (Python, PIL, ffmpeg), cut to `timing/failure_map.json` (a frame is inside a region when frame / 24 falls in [start, end)). Settings and asset picks: `config/g.json`. **Command:** `.venv/bin/python scripts/g_pass.py S33`

| Shot | Frames | What | Output | Status |
| --- | --- | --- | --- | --- |
| S33 | 3219-3388 | gen1-gen6 over F3 (frames 0-167), building from gen0 through its measured mask, the rest fades out over 36 and the building holds alone for 60 | `takes/g/S33/S33_g.mp4` | kept ([H], human_interventions 29) |

## 2026-10-20T22:50-04:00 — G, E: S33 building hold, hum level

- **G:** `.venv/bin/python scripts/g_pass.py S33` (fade 36, alone 60). Output `takes/g/S33/S33_g.mp4`, pending [H]. Its row is in the G table appended above.
- **E:** `.venv/bin/python scripts/e_edit.py main --jobs 4 --only 37_song_03219`, then reassembled with the hum at −14 dBFS peak. The main cut is 4419 frames (184.1 s); the review copy was rebuilt.
- **Status:** rough cut 2, pending [H].

## 2026-10-20T23:05-04:00 — E: cold open back on the porch

- **Fix:** `shot_at(f, cold)` in `scripts/e_edit.py` ignores `config/edit.json` "cuts" for the cold open.
- **Command:** `.venv/bin/python scripts/e_edit.py main --jobs 4 --only 00_cold_open`, then reassembled; the review copy was rebuilt. The main cut is 4419 frames (184.1 s).
- **Status:** rough cut 2, pending [H].

## 2026-10-20T22:36:36-04:00 — G: glitch and decay passes (S33)

- **Tool:** `scripts/g_pass.py` (Python, PIL, ffmpeg), cut to `timing/failure_map.json` (a frame is inside a region when frame / 24 falls in [start, end)). Settings and asset picks: `config/g.json`. **Command:** `.venv/bin/python scripts/g_pass.py S33`

| Shot | Frames | What | Output | Status |
| --- | --- | --- | --- | --- |
| S33 | 3219-3388 | gen1-gen6 over F3 (frames 0-167), building from gen0 through its measured mask, the rest fades out over 36 and the building holds alone for 60, the last 24 after the song | `takes/g/S33/S33_g.mp4` | pending [H] |

## 2026-10-20T23:20-04:00 — G, E: S33 past the song

- **G:** `.venv/bin/python scripts/g_pass.py S33` (fade 36, alone 60, tail 24; 194 frames). Output `takes/g/S33/S33_g.mp4`, pending [H]. Its row is in the G table appended above.
- **E:** `.venv/bin/python scripts/e_edit.py main --jobs 6 --only 37_song_03219 38_S33_tail 39_S34 40_S35 41_S36 42_vote` (the bookends were renumbered), then reassembled; the review copy was rebuilt. The main cut is 4443 frames (185.1 s).
- **Status:** rough cut 2, pending [H].

## 2026-10-21T02:42Z — S35: FEC captures, chat render; E: S35 and the vote card

- **FEC:** `node scripts/fec_capture.mjs` captured 10 fec.gov pages (`config/fec.json`): screenshots in `takes/s35/fec/`, text in `docs/fec/` (the receipts pages' text in `takes/s35/fec/`). Findings and links are in `docs/fec/README.md`.
- **O:** `.venv/bin/python scripts/o_data.py` (adds the chat), then `node scripts/o_render.mjs takes/s35/chat 0 150 1920 1080 "scene=chat"`.
- **E:** `.venv/bin/python scripts/e_edit.py main --jobs 4 --only 40_S35 42_vote`, then reassembled; the review copy was rebuilt. The main cut is 4671 frames (194.6 s).
- **Status:** rough cut 2, pending [H]. S03 is still a placeholder.
