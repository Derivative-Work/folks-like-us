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
