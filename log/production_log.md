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
| S12_v7 | 2002 | 0.92 | renders/b/keyframe/S12/beauty/00880.png, takes/stills/kept/singer.png | `takes/keyframes/S12/S12_v7_s2002.png` | 106.4 | kept ([H] approved 2026-10-20) |
| S28a_v7 | 2001 | 0.92 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v7_s2001.png` | 77.1 | rejected (agent review, see note) |
| S28a_v7 | 2002 | 0.92 | renders/b/keyframe/S28a/beauty/02373.png | `takes/keyframes/S28a/S28a_v7_s2002.png` | 76.1 | rejected (agent review, see note) |
| S06_v7 | 2001 | 0.96 | renders/b/keyframe/S06/beauty/00420.png, takes/stills/kept/dog.png, takes/stills/kept/singer.png | `takes/keyframes/S06/S06_v7_s2001.png` | 154.2 | rejected (agent review, see note) |
| S06_v7 | 2002 | 0.96 | renders/b/keyframe/S06/beauty/00420.png, takes/stills/kept/dog.png, takes/stills/kept/singer.png | `takes/keyframes/S06/S06_v7_s2002.png` | 153.2 | kept ([H] approved 2026-10-20) |
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
