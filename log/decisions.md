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
