# VRAM plan

Pre-production step 7. The brief says: "Batch by stage, one model at a time: all S, then all V, then all L, then G and O." These are the measured numbers that rule rests on, and the rules for running each stage on this box.

## The box

RTX 5090 with 32 GB of VRAM; 38 GB of RAM plus 32 GB of swap (`log/environment.txt`). ComfyUI v0.42.1 streams weights between RAM and VRAM ("dynamic VRAM loading"), so a model larger than VRAM still runs, but it fills RAM and spills into swap.

## Measured (2026-10-19, one run each)

| Stage | Model | Job | Time | GPU peak | RAM peak | Swap peak |
| --- | --- | --- | --- | --- | --- | --- |
| S | FLUX.2 [dev] fp8, Mistral fp4 text encoder | 1920×1088 still, 28 steps | 50 s (77 s with model load) | 24.7 GB | 34 GB | — |
| V | LTX-2.3 22B distilled fp8 + IC-LoRA Union Control, Gemma fp4 | 1280×704, 97 frames (4.0 s), 8 steps | 43 s | 32.1 GB | 37.0 GB | 5.3 GB |
| L | LTX-2.3 22B dev fp8 + distilled LoRA, two passes with the x2 latent upscaler, Gemma fp4 | 1280×704, 97 frames (4.0 s) from one image and 4 s of vocal | 43 s | 31.9 GB | 36.6 GB | 7.1 GB |

Without the 32 GB swap (4 GB before), the V and L runs would have run out of memory.

## Rules

1. **One stage at a time, in the brief's order: all S, then all V, then all L, then G and O.** S, V and L each load a different 22–35 GB model, and switching costs a reload of about 30 s and pushes RAM into swap.
2. **Free memory between stages.** `POST /free` with `unload_models` and `free_memory` (`comfy_client.free()`), before the first job of the next stage.
3. **Nothing else on the GPU or in RAM during S, V and L.** No Blender renders and no browser renders (O) in parallel. Blender plates for a batch are rendered before the batch. G and O are CPU and ffmpeg work and can overlap each other, but not a ComfyUI batch.
4. **Clip length:** V at up to 97 frames (4 s) per run, the length measured here. Longer shots are split at a cut or an 8n+1 frame boundary and joined in E. L follows the sung line, at most 9 s (the template's default) and measured at 4 s. Try a longer clip once before relying on it, because RAM is the limit.
5. **Budget:** about 11 s of compute per second of footage for V and for L, per take. The song's V and L shots total about 100 s of footage. At three takes each, that is roughly an hour of generation per stage.
6. **Watch swap.** If a job pushes swap past about 20 GB, drop to fewer frames per run rather than adding swap: heavy swapping slows every step.

## Findings for the V and L stages

- **V copies its first frame.** With the template's MoGe depth and the Blender beauty frame as the first frame, the output kept the stand-ins' blocky look. V's first frame must be a photoreal keyframe, made with FLUX.2 from the plate and the approved character sheets.
- **The Blender depth pass isn't yet in the control format the IC-LoRA expects.** Fed directly, the output reproduced the gray depth image. Either match MoGe's depth convention or run MoGe on the plate. Decide at the start of V.
- **L keeps the approved singer's identity** from a single image and drives the take from the vocal. The input image needs the mouth well inside the frame.

Test outputs: `takes/v/test/` (git-ignored). Commands: `scripts/ltx_v.py`, and the L test in the production log.
