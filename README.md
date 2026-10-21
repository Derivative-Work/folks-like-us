# Folks Like Us

**AI-generated satire.** A three-minute campaign ad for an invented super PAC, made for the 2026 US midterms. A country-pop jingle about a small town keeps almost saying what the PAC is paying for and swerving at the last second, while a windowless data center grows behind every shot and nobody looks at it. The only honest line is the disclaimer.

Folks Like Us PAC and Folks Like Us Too PAC are fictional, and so is everyone on screen. The real money behind AI-industry super PACs is on the closing fact card, and the sources are in [`docs/fec/README.md`](docs/fec/README.md).

This repository is the production log the video's credits point to. Claude Code produced the video. A human approved or rejected each take, judged everything that needed ears or moving pictures, and made the one screen capture. Every human action is logged.

> **A note from the human:** Election Day is November 3, 2026. Please make a plan to vote: [vote.org](https://www.vote.org).

## How it was made

| Stage | What | Tools |
| --- | --- | --- |
| Song | Lyrics written with Claude; one Suno generation, sung as written; then a cleanup ("deslop") mastering model, kept where it failed | Suno (v6), music-deslop M6f |
| B | The town as stand-in geometry, for camera, layout and depth passes | Blender 5.2 |
| S | Reference stills and per-shot keyframes | FLUX.2 [dev] in ComfyUI |
| V | Every shot, as video-to-video over the Blender depth pass | LTX-2.3 with the IC-LoRA union control |
| L | Lip-sync of the singer | LatentSync 1.6 |
| G | The three glitches where the mastering model broke (six fingers, a frozen smile, a copy-of-a-copy decay) | Python, FLUX.2, LTX-2.3 |
| O | All legible text: captions, signs, mugs, counters, cards | HTML rendered by Puppeteer, tracked onto the shots with OpenCV |
| E | Compositing, grade, edit, mux | Python (NumPy, Pillow), ffmpeg |
| H | Approvals, the Suno screen recording, the final checks | a human |

Three things come straight from the process rather than being staged:
- **The glitches.** The jingle breaks in three places where the cleanup model failed, and the closing spectrogram shows those failures.
- **The fact-card figures.** They come from news reports and the real FEC filings.
- **The planning chat.** The closing screen recording shows the chat where this was planned, including its own suggestion to show itself.

## Where things are

- [`log/production_log.md`](log/production_log.md): every generation and render, with model, prompt, seed, inputs, output and whether it was kept.
- [`log/human_interventions.md`](log/human_interventions.md): every human action, in the human's words.
- [`log/decisions.md`](log/decisions.md): every deviation from the brief, and why.
- [`config/`](config/): prompts, shot timings, the takes that were picked, and every edit setting.
- [`scripts/`](scripts/): one script per stage. Each one documents itself at the top.
- [`docs/planning_chat/`](docs/planning_chat/): the planning chat, as Markdown and as the raw share snapshot.
- [`docs/fec/`](docs/fec/): the FEC pages behind the fact card, with links to check them.
- [`docs/mastering/`](docs/mastering/): the mastering model's report.

## Reproducing it

Large files (audio, takes, renders, the videos) are not in git. The release [`archive-2026-10-21`](https://github.com/Derivative-Work/folks-like-us/releases/tag/archive-2026-10-21) has:
- the two upload files;
- the inputs that can't be regenerated: the song, its stems and masters, the Suno screen recording and the FEC screenshots;
- every take, keyframe and still the production made.

```sh
scripts/setup_env.sh          # the environment: Blender, ComfyUI and pinned weights, LatentSync, Node (idempotent)
scripts/rebuild.sh --fetch    # download the archive, re-render overlays and the edit, check against the release
```

`rebuild.sh` rebuilds both videos from the archived takes. On the production machine that rebuild is byte-identical.

Regenerating the takes themselves from the models is a per-stage job. The commands are in the production log, and the picks in `config/` make the same choices again.
- On the production machine (RTX 5090), re-running a still, a V take and a lip-sync with the same seed gave bit-identical output, and the Blender depth pass was identical.
- On other GPUs or drivers, expect small differences.
- The song can't be regenerated: Suno doesn't give the same song twice.
- The FEC pages are live and will change. The archive keeps what they showed on October 21, 2026.

## Credits

Lyrics by Claude. Music by Suno. Video by Claude Code. Fonts: Oswald, Lora, Caveat, Source Sans 3 and Source Code Pro, all under the SIL Open Font License (`assets/fonts/`). The models are used under their own licenses.
