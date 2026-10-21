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

- **Lyrics:** Claude.
- **Music:** Suno v6, one generation, sung as written.
- **Mastering:** music-deslop (M6f, 10k steps), a post-filter model for AI-generated music that Claude Code built and trained from a human-written spec, on Creative Commons audio only. The model is private for now.
  - The video uses the model's output with its fallback turned off (`--no-fallback`), so the three places where the model fails stay in. Those failures are the glitches F1–F3 and the closing spectrogram.
  - The cold open uses the default master, which hands those passages back to the unprocessed song.
  - The model's report is in [`docs/mastering/REPORT.md`](docs/mastering/REPORT.md).
- **Video:** Claude Code with Claude Opus 5.5, with the models and tools under [How it was made](#how-it-was-made), each used under its own licence.
- **Fonts:** [Oswald](https://github.com/googlefonts/OswaldFont), [Lora](https://github.com/cyrealtype/Lora-Cyrillic), [Caveat](https://github.com/googlefonts/caveat), [Source Sans 3](https://github.com/adobe-fonts/source-sans) and [Source Code Pro](https://github.com/adobe-fonts/source-code-pro), SIL Open Font License 1.1 (`assets/fonts/`).

### Mastering model training data

The music-deslop model was trained only on audio from these datasets, each licensed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). The audio was cut into segments, made stereo, mixed and processed to make training pairs: reverb, EQ, compression, mastering, codecs and other degradations. No dataset audio is in this repository or in the video.

- **Slakh2100** (redux mixes). Ethan Manilow, Gordon Wichern, Prem Seetharaman and Jonathan Le Roux, "Cutting Music Source Separation Some Slakh: A Dataset to Study the Impact of Training Data Quality and Quantity", IEEE WASPAA 2019. https://zenodo.org/records/4599666
- **VocalSet 1.2.** Julia Wilkins, Prem Seetharaman, Alison Wahl and Bryan Pardo, "VocalSet: A Singing Voice Dataset", ISMIR 2018. https://zenodo.org/records/1442513
- **CSTR VCTK Corpus 0.92.** Junichi Yamagishi, Christophe Veaux and Kirsten MacDonald, "CSTR VCTK Corpus: English Multi-speaker Corpus for CSTR Voice Cloning Toolkit (version 0.92)", University of Edinburgh, The Centre for Speech Technology Research, 2019. https://doi.org/10.7488/ds/2645

The degraded training inputs were also made with:
- the [ACE-Step 1.5 VAE](https://huggingface.co/ACE-Step/Ace-Step1.5) (MIT);
- the [Descript Audio Codec](https://github.com/descriptinc/descript-audio-codec) (MIT);
- FFmpeg (LAME, the native AAC encoder and libopus).

No generator output (Suno, ElevenMusic or ACE-Step songs) was used for training.
