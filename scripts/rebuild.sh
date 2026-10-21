#!/usr/bin/env bash
# Rebuild both videos, the captions and the thumbnail from the production archive (scripts/archive.sh): restore the
# archived takes and inputs, then re-run the deterministic stages (O overlays, S03, E edit, export_srt, thumbnail) and
# check the results against the release's checksums.
# Regenerating the takes themselves from the models is per stage: see README.md and log/production_log.md.
#
# Usage: scripts/rebuild.sh [--fetch]   (--fetch downloads the release with gh; otherwise archive/ must hold the parts)
# Needs the environment from scripts/setup_env.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
TAG=archive-2026-10-21
A=archive
if [[ ${1:-} == --fetch ]]; then
  mkdir -p $A
  gh release download $TAG -R Derivative-Work/folks-like-us -D $A --clobber -p '*.tar' -p SHA256SUMS
fi
(cd $A && sha256sum -c --ignore-missing SHA256SUMS)
for t in $A/*.tar; do tar -xf "$t"; done
.venv/bin/python scripts/o_data.py
scripts/o_render_all.sh 8
.venv/bin/python scripts/e_s03.py
.venv/bin/python scripts/e_edit.py all --jobs 8
.venv/bin/python scripts/export_srt.py
.venv/bin/python scripts/thumbnail.py
ln -f takes/e/folks_like_us_main.mp4 $A/folks_like_us_youtube_1080p24.mp4
ln -f takes/e/folks_like_us_vertical.mp4 $A/folks_like_us_shorts_1080x1920.mp4
cp deliverables/folks_like_us.en.srt deliverables/folks_like_us_thumbnail.jpg $A/
(cd $A && grep folks_like_us SHA256SUMS | sha256sum -c -)
