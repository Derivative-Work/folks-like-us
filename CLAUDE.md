# Folks Like Us

An AI-generated campaign-ad satire for an invented super PAC. The agent does the production; a human approves or rejects takes, judges anything that needs ears or moving pictures, and makes screen captures.

**Start here:** the brief is the Claude Doc https://claude.ai/artifact/S37uBB1UQJGfxSWx7wQ6Ek (read it with the docs tools, not a web fetch). Then read the latest entries of `log/production_log.md`, `log/human_interventions.md` and `log/decisions.md`.

- **Environment:** `scripts/setup_env.sh` (idempotent; `--check-only` verifies). ComfyUI and its weights live in `~/ComfyUI`, outside the repo. Start it with `~/ComfyUI/.venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1`.
- **Logs:** `log/production_log.md` gets one entry per generation or render: shot ID, stage code, model and version, prompt, seed, inputs, output, kept or rejected. Every human action goes in `log/human_interventions.md`. Any deviation from the brief goes in `log/decisions.md`.
- **Large files** (audio, renders, weights, frame sequences) stay out of git. Log the command that regenerates them instead.
- **Audio:** `audio/track/` holds the Suno one-shot and stems; `audio/master/folks_like_us_master_nofallback.wav` is the master (music-deslop M6f 10k, `--no-fallback`).
