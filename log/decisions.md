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

## 2026-10-19 — Stops are not made; the shots reflow over the vocal gaps (supersedes "All four stops are made in the edit")

- **The human** rejected the made silences by ear (human interventions 6). The take keeps its own timing, so edit time = source time, with no inserts.
- **The brief, updated** (doc rev 11 → 26):

  | Shot | Stop | Vocal gap | Was | Now |
  | --- | --- | --- | --- | --- |
  | S10 | ST1 | 1.06 s | freeze in silence | the picture freezes while the band plays on, releasing on "—day." |
  | S16 | ST2 | 1.19 s | "Silence." | the plane gag plays over the band |
  | S21 | ST3 | 0.12 s | freeze and caption swap | no freeze; "data centers" types across "everything, everything, every single thing", is deleted on "but—", and "you" types as he sings "—you!" |
  | S22 | ST3 | | "Unfreeze on…" | hard cut on "—you!" |
  | S30 | ST4 | 1.33 s | "Clean silence", "held twice as long" | the band plays on, the singer opens and closes his mouth, the cursor's "A" hesitation fills the gap, and "apple pie" types as he sings it |

- **Elsewhere in the brief:** the E pipeline row no longer lists "silences". The stop-map task records the result. The rough-cut checkpoint reads "all four stop gags land over the vocal gaps". The open items for the stops, the outro, the deslop log and S23 are answered and ticked, and the first review checkpoint is ticked.
- **In the repo:** `scripts/stop_map.py` now only measures (`timing/stops.json` has no edit ops), and `style/style_spec.md` uses the take's own timing.

## 2026-10-19 — The cold open's hook uses the with-fallback audio

- **Human decision** (human interventions 8): S01 doesn't show the F1 glitch.
- **The agent's reading:** this covers the sound as well as the picture. The no-fallback master carries the F1 artifact, so S01 takes its hook audio from `audio/master/with-fallback/folks_like_us_master_withfallback.wav` for the same span (F1 is 97% faded there). It is the same take with the same timing, so S29–S31's lip sync holds, and S01 has no G pass. The first time F1 is seen or heard is S29.
- **Brief:** S01's row and the open item are updated (doc rev 26 → 28).

## 2026-10-19 — Set kit: the building grows as a campus; layout and shot choices the brief left open

- **The building is a data-centre campus:** 20 identical gray, windowless halls along one line north-north-east of the farm (azimuth 30°). Each stage adds halls nearer the farm:

  | Stage | Nearest hall | Notes |
  | --- | --- | --- |
  | B1 | 2.96 km | one hall on the horizon, cranes at the future site |
  | B2 | 1.31 km | cranes gone |
  | B3 | 260 m | in the diner window |
  | B4 | 110 m | its fence about 25 m from the house |

  The brief has one asset placed at B1–B4. A growing campus gives the same four looks ("small on the horizon", "nearer, cranes gone", "fills the diner window", "fills the frame behind the porch"), keeps every earlier view consistent, and puts the "cornfield used to stay" where halls replace corn. All halls, masts, lamps, LEDs and fences write the `building_mask` AOV.
- **B3 at 250 m, not the first-built 400 m.** From the diner the nearest 400 m hall sat outside the window's view, so B3 starts at the 260 m hall.
- **Montage and split shots:** S27 is five equal cuts of about 0.44 s each (Grandma at the kitchen window, the kid with the tangled kite, the diner patrons, the cows, the leash on the fence). S28 is two cuts of about 0.4 s (marquee, then the water-tower gauge), since one frame can't hold both.
- **S31 is shot from the porch looking south.** That way the building, behind the camera, is what the pie tin reflects (brief: "with the building reflected in the tin"). Eevee doesn't reflect what is off screen, so the reflection itself comes from V or O.
- **Held-note cues:** S13 and S25 ("aiming high (tail)") start at the middle of the held "high", because "Gonna" follows with no gap (`mid:` cues in `config/shot_cues.json`).

## 2026-10-19 — Set-kit fixes after [H]'s keyframe review

[H] found four props that were wrong in the Blender set itself, so the fix is in `scripts/blender/build_town.py` and every affected layout was re-rendered, not patched in the keyframes:

- **Water tower:** a cylindrical steel tank under a conical roof on 31 m legs (it was a squashed sphere). This is the classic farm-town tower; the brief names the tower but not its shape.
- **Porch rail:** a wide flat board (`RAIL_TOP` 1.58 m, 0.3 m deep), so the pie and mug in S31 sit on top of it. The rail was 8 cm wide, narrower than the pie, and both props sat 4 cm into it.
- **Flag:** the pole leans 35° out from the right porch post and the flag hangs from it. The pole leaned back toward the house, and the flag was a separate sheet in mid-air.
- **Leash (S27e):** it hangs straight down from where it is tied on the fence, with the empty collar just above the grass. It was a rigid rod at 60°.

Keyframe prompts now also name what the stand-ins become where FLUX.2 kept them as blocks: white clapboard siding on the porch shots, real corn, the S04 bunting sign and cranes, and the S28a massing as one church (`config/keyframes.json`, v7–v9).

## 2026-10-20 — V: people follow their stand-ins loosely (S12, S17, S19)

The brief's V stage runs LTX-2.3 over the Blender set kit. The kit's people are rigid stand-ins, so at full control strength a take can only slide or hold them: S12's walk slid, S17's grandmother never moved, and S19's hand copied a cylinder arm ([H] rejected all three). These shots now follow the depth at reduced strength (`"guide"` in `config/v.json`: S12 0.5, S17 0.4, S19 0.5). The set and the camera move still come from the kit; the person's motion comes from the prompt. Rigging and animating the stand-ins in Blender was the alternative; it was not needed.

## 2026-10-20 — S17: no kitchen dim (superseded below)

The brief has the kitchen lights dim as grandma pulls the pie, on "apple pie". Generated, the dim repeated in every chained clip (the take faded down, up and down again). The take is now generated with steady light, and E darkens it once, starting on the second "pie!" (59.073 s), to about half brightness over 1 s. That also puts the dim exactly on the word.

## 2026-10-20 — S17: the kitchen dim is cut

[H] watched the graded dim in context and said it doesn't work: removed. S17 plays with steady kitchen light; E applies no grade to it. This drops the brief's running gag "Kitchen dims on 'apple pie'". S18's bulb dimming over the bill is a separate gag and stays.
