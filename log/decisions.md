# Decisions

Append-only. Every deviation from the brief (https://claude.ai/artifact/S37uBB1UQJGfxSWx7wQ6Ek), with the reason.

## 2026-10-19 — ComfyUI workflows and Blender scripts are written here, not adapted from Read-Only

- **Brief:** "The ComfyUI API workflows and Blender scripts from Read-Only, to adapt per shot type."
- **Instead:** Read-Only isn't done yet (human, 2026-10-19), so this project builds its own, starting from ComfyUI's FLUX.2 and LTX-2.3 templates.

## 2026-10-19 — Models chosen for S, V and L

- **S:** FLUX.2 [dev], fp8 diffusion model with the fp4 Mistral text encoder.
- **V:** LTX-2.3 IC-LoRA Union Control on the distilled fp8 checkpoint. It conditions on depth, normals or edges, which the Blender set kit renders.
- **L:** LTX-2.3 image+audio-to-video (IA2V) on the dev fp8 checkpoint. The brief said "check what's current"; on 2026-10-19 this is ComfyUI's native audio-driven lip sync, and it shares weights with V.
- **Why the small variants:** the 5090 has 32 GB of VRAM, and the box has 38 GB of RAM and 4 GB of swap.
- Pinned revisions are in `config/models.tsv`, and the setup in `scripts/setup_env.sh`.

## 2026-10-19 — F1–F3 candidates come from the mastering model's own log

- The brief's open item ("Does the deslop model log where it fails?") is answered yes: `docs/mastering/fallback.json` lists the passages where the fallback would have stepped in.
- folks-like-us: 103.437–106.094 s (F1), 124.894–130.757 s (F2), 133.707–141.088 s (F3). They match the brief's three regions by position.
- These are candidates. [H] still confirms every boundary by ear (brief, failure map).

## 2026-10-19 — All four stops are made in the edit

- **Brief:** "For each of the four stops, measure whether the Suno take actually goes silent… A made silence is an edit, so log it in decisions.md."
- **Measured** (`timing/stops.json`): the take has no silence at any stop. Suno paused only the vocal (ST1 1.06 s, ST2 1.19 s, ST3 0.12 s, ST4 1.33 s), and the band plays through at −12 to −37 dB. ST1 even has a drum fill.
- **The edit** (all times in source seconds):

  | Stop | Mute | Insert | Silence |
  | --- | --- | --- | --- |
  | ST1 | 33.340–34.370 | none | 1.03 s |
  | ST2 | 54.480–55.643 | none | 1.16 s |
  | ST3 | 85.287–85.378 | one beat (0.72 s) at 85.287 | 0.81 s |
  | ST4 | 106.380–107.683 | one beat (0.72 s) at 106.380 | 2.02 s |

  - Each mute runs from the setup word's end to 30 ms before the swerve word, with 10 ms ramps.
  - ST4 is held about 1.8× ST1 and ST2, the brief's "twice as long" in whole beats.
  - Inserts are whole beats, so the groove resumes on the grid. They push everything after them later, by 0.72 s after ST3 and 1.44 s after ST4. The edit runs 142.64 s; `stops.json` has the source-to-edit time map.
- **Why mute in place rather than cut:** the swerve words and the music under them keep their original timing, so the timing map stays valid except for the two inserts.
- [H] judges the result at the rough-cut checkpoint. `audio/master/preview_stops.wav` lets them hear it now.
