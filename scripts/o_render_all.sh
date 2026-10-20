#!/usr/bin/env bash
# O: render every overlay layer (scripts/o_render.mjs, overlays/folks.html) into takes/o/ (git-ignored, regenerable).
#   surface/<shot>/NNNNN.png   text on the shot's tracked surfaces, frame = the take's frame (stage = take x 1.5)
#   screen/NNNNN.png           the screen layer over the song, frame = song frame (0-3388)
#   screen_nojitter/           S29-S31 without the F1 jitter, for the S01 cold open
#   screen_portrait/           S29-S31 for the vertical cut (1080x1920)
#   cards/<name>/              title, s34, fact (1920x1080) and labelcard (1080x1920), frame = card frame
# Runs JOBS renders at once. Usage: scripts/o_render_all.sh [JOBS=6]
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS=${1:-6}
.venv/bin/python scripts/o_data.py
jobs_list=()
frames() { python3 -c "import json;print(len(json.load(open('takes/o/tracks/$1__$2.json'))['quads']))"; }
add() { jobs_list+=("$*"); }
for shot in S05 S08 S09 S14 S15 S16 S18 S19 S26 S28a S28b S31; do
  name=$(python3 -c "import json;print(next(s['name'] for s in json.load(open('config/o.json'))['surfaces'] if s['shot']=='$shot' and s['style']!='tv'))")
  add "takes/o/surface/$shot 0 $(frames $shot $name) 1920 1056 scene=surface&shot=$shot"
done
add "takes/o/surface/S31v 0 $(frames S31v mug) 1056 1920 scene=surface&shot=S31v"
add "takes/o/surface/S24 0 $(frames S05 mug) 1920 1056 scene=surface&shot=S05&as=S24"
add "takes/o/surface/S25 0 $(frames S19 chair_tag) 1920 1056 scene=surface&shot=S19&as=S25"
add "takes/o/surface/S17i 0 1 1920 1088 scene=surface&shot=S17i"
for a in 0 850 1700 2550; do b=$((a + 850)); [ $b -gt 3389 ] && b=3389; add "takes/o/screen $a $b 1920 1080 scene=screen"; done
add "takes/o/screen_nojitter 2392 2691 1920 1080 scene=screen&nojitter=1"
add "takes/o/screen_portrait 2392 2691 1080 1920 scene=screen&portrait=1"
add "takes/o/cards/title 0 120 1920 1080 scene=title"
add "takes/o/cards/s34 0 144 1920 1080 scene=s34"
add "takes/o/cards/fact 0 360 1920 1080 scene=fact"
add "takes/o/cards/labelcard 0 72 1080 1920 scene=labelcard"
# No shell between xargs and node: the queries contain "&".
printf '%s\n' "${jobs_list[@]}" | xargs -L 1 -P "$JOBS" node scripts/o_render.mjs
