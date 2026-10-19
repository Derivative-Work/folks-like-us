# Style spec

From the brief's Look line: golden-hour campaign-ad gloss, warm grade, slow push-ins, lens flare. One invented singer, one invented town. Every B, S, V and L pass follows this file. A change to it is a decision (`log/decisions.md`).

No real political ads are downloaded or archived as references (brief). The look is described here in words and numbers only.

## Format

| Setting | Value |
| --- | --- |
| Frame rate | 24 fps. Cuts land on whole frames: cut frame = round(edit time × 24). |
| Main video | 16:9. Working resolution 1920×1080; the delivery resolution is decided at the final cut. |
| Vertical cut | 9:16, 1080×1920. Reframed in B with its own cameras, never cropped (brief). |
| Shutter | 180° (motion blur of 1/48 s) in Blender. Generated video matches it. |
| Audio timeline | Edit time from `timing/stops.json` (source time plus the ST3 and ST4 inserts). |

## Light

- **Key:** low sun, 8–12° above the horizon, warm (about 3200 K as seen on camera). It lights faces from the side, at three-quarters, never straight on.
- **Fill:** sky blue, about 2 stops under the key, so shadows stay open and slightly cool.
- **Back light:** the sun rims hair, flannel and the dog's coat. Dust or pollen in the air catches it.
- **Interiors** (kitchen, diner): warm practical lights plus low sun through the windows.
- **Escalation:** the building's light takes over. The cool white of its LED and floodlights (about 5600 K, slightly green) grows from a speck at B1 to the porch's main light at B4 (running-gags table).

## Camera

- **Lenses:** 35 mm for wides, 50 mm for mediums, 85 mm for close-ups (full-frame equivalents).
- **Depth of field:** shallow, f/2–2.8 on mediums and close-ups. The background is soft but readable: the building must read in every shot, even out of focus.
- **Movement:** slow push-ins, 3–8% of frame width per second, and slow lateral dollies. No handheld shake and no whip pans. A move starts and ends on a beat where possible (`timing/timing_map.json`, `beats`).
- **Height:** eye level or slightly low, the heroic campaign angle. The singer is framed center or on the left third.
- **Lens flare:** occasional. At most one flare per section, from the sun or later the building's floodlights, always in B (an optical element), never painted in post.

## Grade

- Warm highlights and slightly teal shadows. Lifted blacks at about 3% (a soft "film" toe), with gentle highlight roll-off.
- Saturation: rich ambers, greens and flag colours. Skin stays natural.
- A light halation glow around highlights and fine grain, applied evenly in E so V and B shots match.
- The building is the exception: neutral gray and cold in every grade. It never warms up.

## Town palette

Barn red, cornfield gold, sky blue, white clapboard, flag red, white and blue. The building is the only flat, windowless, gray object.

## On-screen text (O)

- **Campaign typography:** a bold condensed sans for PAC names, lower thirds and yard signs, and a friendly serif for the cards. Both are SIL OFL fonts, bundled in `assets/fonts` (to choose).
- **Lower thirds:** navy bar with a thin red rule and white text. "Folks Like Us PAC" and "Folks Like Us Too PAC" use the same font and colours (brief).
- **Karaoke captions:** bottom center, white with a soft shadow. Caption swaps use one template (brief).
- **"AI-generated satire" label:** small, top-right, from the first seconds (brief guardrails).
- All legible text goes in through O as a composited layer, never rendered by V (brief).

## Generation prompts (S, V, L)

Shared fragment, added to every prompt:

> golden hour, low warm sun, cinematic campaign advertisement, shallow depth of field, 35mm film look, soft halation, gentle lens flare, warm color grade, American small town

Shared negative prompt:

> text, letters, logo, watermark, signage text, readable writing, real person, celebrity, politician, flag text, distorted hands, extra fingers, oversaturated, harsh shadows

The singer, Grandma and the kid come from the approved character sheets (step 6). A take that drifts toward a recognizable person is rejected (brief).
