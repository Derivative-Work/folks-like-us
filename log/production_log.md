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
