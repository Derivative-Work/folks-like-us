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

## 2026-10-20 — L: LatentSync 1.6 on the V takes, outside ComfyUI

Pre-production picked LTX-2.3's image+audio-to-video for L (above, "L"). It makes a new clip from one image, and the singing shots already have approved V takes with their own motion and camera moves, so L had to sync the lips of those takes. Tried with LTX-2.3's audio-video model on S22 and then on all eight L shots:

- Regenerating only a mask around the face, with the vocal fixed: the mouth held the V grin at every strength, with or without modality guidance (the A/V coupling boost).
- Re-denoising the whole frame from sigma 0.9875 with modality guidance 3, then compositing the face back: S22 synced well, but across the eight shots only some seeds synced, and the head moved away from the V take's body (S12, S15, S29), so the pasted face missed.

The brief says "check what's current". The current local tool for re-syncing existing footage is LatentSync 1.6 (ByteDance; a May 2026 comparison still ranks it first for this). It regenerates only the lower face, so each L take is its approved V take with new lips. Two deviations follow:

- **Not via ComfyUI.** The brief names ComfyUI for L. The ComfyUI wrapper would install LatentSync's pinned packages (diffusers 0.32.2, mediapipe, decord, insightface) into ComfyUI's venv; it runs instead from ByteDance's repo in its own venv (`~/LatentSync`, `scripts/setup_env.sh`), with torch 2.8 cu128 in place of its pinned 2.5.1, which has no RTX 5090 kernels.
- **25 fps.** LatentSync works at 25 fps. The 24 fps frames are labelled 25 fps and the vocal is sped up by 25/24 to match, so each frame keeps its own audio and the take comes back frame for frame at 24 fps.

Guidance 2.5 (the default 1.5 barely moved the lips off the V grin; 3.5 smeared them pink). LatentSync skips faces under 50×80 px, so it runs on a 512 px crop that follows the face (S12 starts far away), pasted back through a feathered ellipse.

## 2026-10-20 — G: what the glitch passes do, where the brief can't be followed literally

- **S29's wrong-way flag is cut.** The brief puts "the flag's stripes ripple the wrong way" inside F1. In the approved S29 and S29v takes the flag is out of frame (only its pole shows at the top right), so there is nothing to ripple. Reframing would mean re-doing approved V and L takes for a two-second effect; the other F1 effects (six fingers, the server-rack sky, the caption jitter) carry it.
- **Six fingers are FLUX.2 edits, picked by count.** Asked for six fingers, FLUX.2 mostly drew five. One edit per shot clearly has six digits (S29: five fingers and a thumb; S29v: four fingers and a thumb on each side), and it is pasted on all three of that shot's two-frame flashes. The V sign becomes a spread hand with one digit too many.
- **One frame of server racks fills the sky as the depth pass finds it** (the plate's farthest depth). In S29v that is a strip along the top; the take's own sky reaches a little lower.
- **S32 is S33's approved keyframe, held.** The brief gives S32 (the 22 s disclaimer) no B or V: "the singer holds a frozen smile". It holds S33's 1920 px keyframe with a slow push-in to 1.6x, so the face is large by F2 and the tag cuts straight into the outro's decay from the same porch. F3 begins 0.43 s before S33 (133.707 s), so its last 10 frames are re-encoded lossier each frame.
- **S33's decay is six generations**, each the previous one re-encoded at half size (x264 crf 36) and then re-denoised by LTX-2.3 at 0.45. The shot ramps from generation 1 to 6 across F3, the building is composited back from the approved take through its mask pass, and over the last second everything else fades to black, ending on the building alone. The last 3 frames fall after F3 ends (141.088 s); they are the building alone on black.

## 2026-10-20 — O: text placement, and where the brief left choices open

- **Text is tracked on the takes, not pinned to Blender's anchors.** V follows the layout loosely: hand-held mugs sit where the hand is, the S20 TV wall is larger than the layout's, and the S08 signs moved. Each surface is placed by hand on a frame of its approved take and tracked through it (`scripts/o_track.py`); S18's bill, whose room goes dark, is keyframed instead. Ink is composited by multiply, so it takes the shot's light.
- **The "AI-generated satire" label stays on screen for the whole film,** top right, not only for the 5 s after the title card (S02). The guardrail asks for it "from the first seconds, not only in the fine print"; keeping it on throughout satisfies both lines.
- **The diner TVs (S20, S23) are composited in E, not O.** They show moving pictures (the approved takes), keyed to the screens' dark pixels so the diners' heads stay in front. That is picture compositing; O's renderer draws text.
- **Invented copy where the brief gives none:** the bill's utility ("Hometown Power & Light", line items, $187.42 ticking to $1,146.08), the title card's subtitle ("A message from people like you, about people like you"), and S32's fine print (`config/o.json`). None names a real person or organisation.
- **Gauges:** the water gauge is lettered (FULL to EMPTY, the arrow at EMPTY) only in S28b, where the brief needs "empty" read. In S04 and S13 the tower is far away and the gauge is a sliver at its edge; its fill level comes from B.
- **S18's mug** is at the frame edge with about 60 px showing, so "Folks Like Us" is stacked on three lines.
- **S15's "A I"** is small, in the patch of sky past the porch roof (the only sky in the approved take). S16, all sky, carries the large letters, and its "I" smears through ST2.
- **The vertical cut's captions reflow** to a 1080-wide column higher in the frame (brief), and it ends on a two-second label card.
- **Fonts** (style spec: "to choose"): Oswald (condensed sans: PAC names, lower thirds, signs), Lora (serif: cards, mugs), Caveat (handwriting: the tag and the recipe card), Source Sans 3 (captions, fact card). All SIL OFL, in `assets/fonts` with their licences.

## 2026-10-20 — E: the rough cut's construction

- **S10, S21 and S30 are lip-synced from approved takes.** The brief gives them only E and O, but each shows the singer singing. S10 is S05's porch take (LatentSync, as L), frozen mid "data—" until "—day."; S21 is S19's kitchen take singing "everything, everything, every single thing but—"; S30 holds S29's last frame and, over the ST4 gap, silently mouths the next line ("It's apple…"), which reads as "opens his mouth and closes it".
- **S07 is the approved Granddad photo still with a push-in** (brief: S, E), not a generated move.
- **S20's TV ads** are the approved takes plus two new FLUX.2 stills of the singer (a tractor, a ballgame) from his approved sheet; the brief's "a dog, a tractor, a flag, a ballgame".
- **The hum under S33–S36 is synthesised** (60 Hz and harmonics with filtered noise). The outro's music ends at 141.2 s; the brief has the hum continue, and the bookends sit on it.
- **The grade is applied once in E** to every picture shot (halation and grain only; the warm grade is already in the generated pictures).

## 2026-10-20 — E: rough-cut notes from [H] (human_interventions 23)

- **Cuts move off the song's shot times** (`config/edit.json` "cuts"). Each picture stays in song sync, so a shot that now starts later begins part way into its take, and lip-sync and tracked text still line up.
  - S13 runs 980–1030 (2.1 s, was 0.5 s).
  - S16 runs 1308–1368 (2.5 s, was 1.2 s), so the plane and the "A I" smear carry into "It's apple pie!".
  - The S27–S28 montage's seven parts run 0.6–0.75 s each (were 0.4 s), from 2320 to 2424. S29 now starts 1.3 s into "It's two little letters", 2.8 s before the six-finger flash.
- **New V takes for the lengthened shots.** The approved takes were exactly as long as their old slots. The nine shots got new plates and new takes from their approved keyframes and prompts (`config/shots_b.json` "span", seeds 11 and 12). Agent picks, pending [H]:
  - S16 is seed 12: its smoke curls into a ring, the brief's pie shape.
  - The others are seed 11. The S27e leash still hangs straight down.
  - The S16, S28a and S28b text is re-tracked on the new takes.
- **S19c, the close shot, is a crop, not a new take.** It runs on "Well, we don't know a thing about it" (70.08 s to 73.18 s), then cuts to S19's full angle on "don't you ask us".
  - Its source is S19's approved V take played backwards (frames 77 down to 4), so its last frame meets S19's frame 5 at the cut.
  - It is lip-synced as an L extra and cropped in E to the face and the pointing hand (a 448 px region, about 4.3× up, lightly sharpened). It is softer than the wide.
  - S18, the bill, ends there, so the bill stops ticking at about two-thirds of its rise.
- **The TV key tests chroma, not HSV saturation.** Near black, saturation is noise: the darkest screens measured 1.0, failed the key, and stayed empty. The key is now value < 0.34 and value × saturation < 0.16. All nine screens fill, and the diners' heads stay in front.
- **S21 carries S19's TBD tag.** Its source is S19's frames from 0, so the tracked tag lines up frame for frame.
- **S34 is one 8 s shot.** The spectrogram is scaled to 80% under O's line, which fades in at 0.75 s. It was a 4 s plot followed by a 4 s card.
- **The production-log link in the credits** (fact card and label card) is github.com/Derivative-Work/folks-like-us, per [H].
- **The human's closing note.** It comes after the fact card in the main cut (5 s) and after the label card in the vertical (4 s, silent). It reads "A note from the human / Election Day is November 3, 2026. / Please make a plan to vote." The date was checked: the first Tuesday after the first Monday in November 2026.
  - It carries no "AI-generated satire" label: it is the human's own words, not satire, and the label card plays just before it.
  - The vertical cut grows from 14.5 s to 18.5 s (the brief says it ends on the label card).
