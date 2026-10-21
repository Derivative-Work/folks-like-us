#!/usr/bin/env bash
# The production archive (brief: "the full production archive"): what git doesn't hold and can't regenerate, plus every
# take the production made, as tar parts under GitHub's 2 GiB per-asset limit, published as a release of this repo.
#
#   inputs.tar     audio/ (the Suno song, stems, both masters: the mastering model's input and output),
#                  takes/s03/suno_recording.mov ([H]'s screen recording), takes/s35/fec/*.png (the FEC pages as captured,
#                  less the receipts pages),
#                  scenes/town.blend
#   takes-vks.tar  takes/v, takes/keyframes, takes/stills (all candidates), takes/o/tracks, takes/e/people
#   takes-l.tar    takes/l (all takes, crops, vocals; no working frames)
#   takes-g.tar    takes/g (assets, passes, decay generations; no working frames or tests)
#   the two upload files, their captions and thumbnail (deliverables/, also in git), and SHA256SUMS
# Left out: regenerable bulk (renders/, working frame folders, edit segments, overlay renders, review copies) and the
# FEC receipts pages (screenshot and text), which name private donors.
#
# Usage: scripts/archive.sh [--upload]   (builds archive/, git-ignored; --upload publishes the release with gh)
set -euo pipefail
cd "$(dirname "$0")/.."
TAG=archive-2026-10-21
A=archive
mkdir -p $A
skip=(--exclude='*/frames' --exclude='*/frames/*' --exclude='takes/l/*/s[0-9]*/v' --exclude='takes/l/*/s[0-9]*/crop'
      --exclude='takes/l/*/s[0-9]*/out' --exclude='takes/l/*/s[0-9]*/tmp' --exclude='takes/g/*/test_*'
      --exclude='takes/l/test')
tar -cf $A/inputs.tar --exclude='*receipts*' audio takes/s03/suno_recording.mov takes/s35/fec/*.png scenes/town.blend
tar -cf $A/takes-vks.tar "${skip[@]}" takes/v takes/keyframes takes/stills takes/o/tracks takes/e/people
tar -cf $A/takes-l.tar "${skip[@]}" takes/l
tar -cf $A/takes-g.tar "${skip[@]}" takes/g
ln -f takes/e/delivery/folks_like_us_youtube_1080p24.mp4 takes/e/delivery/folks_like_us_shorts_1080x1920.mp4 $A/
cp deliverables/folks_like_us.en.srt deliverables/folks_like_us_thumbnail.jpg $A/
(cd $A && sha256sum inputs.tar takes-*.tar folks_like_us_*.mp4 folks_like_us.en.srt folks_like_us_thumbnail.jpg > SHA256SUMS)
ls -l $A
for f in $A/*.tar $A/*.mp4; do
  (( $(stat -c %s "$f") < 2147483648 )) || { echo "$f is over 2 GiB" >&2; exit 1; }
done
if [[ ${1:-} == --upload ]]; then
  gh release create $TAG -R Derivative-Work/folks-like-us --title "Production archive (2026-10-21)" \
    --notes "The production archive for Folks Like Us: the two upload files, the inputs git doesn't hold, and every take. See README.md (Reproducing it) and scripts/archive.sh for what each part contains." \
    $A/SHA256SUMS $A/folks_like_us_*.mp4 $A/folks_like_us.en.srt $A/folks_like_us_thumbnail.jpg $A/*.tar
fi
