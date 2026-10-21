#!/usr/bin/env bash
# Set up the Folks Like Us production environment on an RTX 5090 box (Ubuntu 26.04).
# Idempotent: rerun it after any failure, and it picks up where it stopped. Downloads resume.
#
# Usage: scripts/setup_env.sh [--no-models] [--check-only]
#   COMFYUI_DIR  where ComfyUI and its weights live, outside the repo (default ~/ComfyUI)
#   LATENTSYNC_DIR  where LatentSync (L) and its weights live (default ~/LatentSync)
#
# What it installs, by pipeline code (brief, "Pipeline codes"):
#   B  Blender 5.2.2 LTS (snap), headless Python
#   S  FLUX.2 [dev] fp8 in ComfyUI
#   V  LTX-2.3 IC-LoRA Union Control (video-to-video from Blender passes) in ComfyUI
#   L  LatentSync 1.6 (its own venv, outside ComfyUI) on the V takes; YuNet face boxes (ComfyUI's OpenCV) for the crops
#   O  Node 24 + Puppeteer + Chrome headless shell (the Ghost in the Machine overlay renderer)
#   G  Python 3.12 venv (uv): NumPy, SciPy, librosa, Matplotlib, WhisperX for the timing map
#   E  ffmpeg 8 with libx264
# Versions match Ghost in the Machine where it used the same tool, so renders stay comparable.
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
COMFYUI_DIR=${COMFYUI_DIR:-$HOME/ComfyUI}
LATENTSYNC_DIR=${LATENTSYNC_DIR:-$HOME/LatentSync}
LATENTSYNC_COMMIT=a229c3948406bc2cf6eaf4873e662e70c6a04746   # bytedance/LatentSync, 2025-06-20
LATENTSYNC_HF_REV=c42c7e6c8e9c213626389fa7d9a3c444b8536353   # ByteDance/LatentSync-1.6
NODE_VERSION=24.22.0
BLENDER_CHANNEL=5.2lts/stable
SWAP_GB=32
COMFYUI_TAG=v0.42.1
TORCH_INDEX_COMFY=https://download.pytorch.org/whl/cu130
# torch as installed and checked on 2026-10-19 (ComfyUI wants a current cu130 build).
# Custom nodes, pinned to the commits current on 2026-10-19.
CUSTOM_NODES=(
  "https://github.com/Lightricks/ComfyUI-LTXVideo 44c8a36b7c31"
  "https://github.com/kijai/ComfyUI-KJNodes f20bdd5337ac"
  "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite 4d907bee61e9"
)

MODELS=1
CHECK_ONLY=0
for a in "$@"; do
  case $a in
    --no-models) MODELS=0 ;;
    --check-only) CHECK_ONLY=1 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

step() { printf '\n== %s\n' "$*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

# nvm only loads in interactive shells.
export NVM_DIR=${NVM_DIR:-$HOME/.nvm}
export PATH=$NVM_DIR/versions/node/v$NODE_VERSION/bin:$HOME/.local/bin:/snap/bin:$PATH

install_system() {
  step "System tools"
  command -v nvidia-smi >/dev/null || die "no NVIDIA driver; install driver >= 570 (Blackwell) first"
  local drv; drv=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
  (( ${drv%%.*} >= 570 )) || die "NVIDIA driver $drv is older than 570, the minimum for the RTX 5090"

  local apt_pkgs=()
  command -v git >/dev/null || apt_pkgs+=(git)
  command -v git-lfs >/dev/null || apt_pkgs+=(git-lfs)
  command -v curl >/dev/null || apt_pkgs+=(curl)
  command -v ffmpeg >/dev/null || apt_pkgs+=(ffmpeg)
  if (( ${#apt_pkgs[@]} )); then sudo apt-get update && sudo apt-get install -y "${apt_pkgs[@]}"; fi
  ffmpeg -hide_banner -encoders 2>/dev/null | grep libx264 >/dev/null || die "ffmpeg lacks libx264"

  command -v blender >/dev/null || sudo snap install blender --channel=$BLENDER_CHANNEL --classic

  command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh

  if ! command -v node >/dev/null || [[ $(node --version) != v$NODE_VERSION ]]; then
    [[ -s $NVM_DIR/nvm.sh ]] || curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
    # shellcheck disable=SC1091
    . "$NVM_DIR/nvm.sh" && nvm install $NODE_VERSION
  fi
}

ensure_swap() {
  # FLUX.2 and LTX-2.3 offload weights to system RAM, and FLUX.2 fp8 is reported to use ~70 GB of it; this box has 38 GB.
  step "Swap (/swap.img, $SWAP_GB GB)"
  local have; have=$(swapon --show=NAME,SIZE --bytes --noheadings | awk '$1=="/swap.img"{print $2}')
  if (( ${have:-0} >= SWAP_GB * 1024**3 * 95 / 100 )); then echo "already ${have} bytes"; return; fi
  sudo swapoff /swap.img 2>/dev/null || true
  sudo fallocate -l ${SWAP_GB}G /swap.img
  sudo chmod 600 /swap.img
  sudo mkswap /swap.img >/dev/null
  sudo swapon /swap.img
  grep -q '^/swap.img' /etc/fstab || echo '/swap.img	none	swap	sw	0	0' | sudo tee -a /etc/fstab >/dev/null
}

install_project() {
  step "Project Python env (.venv, Python 3.12, torch 2.8 cu128, WhisperX)"
  cd "$REPO"
  uv sync

  step "Overlay renderer (Puppeteer + Chrome headless shell)"
  if [[ -f package-lock.json ]]; then npm ci; else npm install; fi
  npx puppeteer browsers install chrome-headless-shell

  # Pre-commit hook: rejects staged files over 50 MiB.
  git config core.hooksPath scripts/hooks
}

install_comfyui() {
  step "ComfyUI $COMFYUI_TAG in $COMFYUI_DIR"
  if [[ ! -d $COMFYUI_DIR/.git ]]; then
    git clone https://github.com/comfyanonymous/ComfyUI "$COMFYUI_DIR"
  fi
  git -C "$COMFYUI_DIR" fetch --tags --quiet
  git -C "$COMFYUI_DIR" -c advice.detachedHead=false checkout --quiet $COMFYUI_TAG
  cd "$COMFYUI_DIR"

  # Its own venv: ComfyUI wants a current torch (cu130), while WhisperX pins torch 2.8.
  [[ -x $COMFYUI_DIR/.venv/bin/python ]] || uv venv --python 3.13 "$COMFYUI_DIR/.venv"
  local pip=(uv pip install --python "$COMFYUI_DIR/.venv/bin/python")
  "${pip[@]}" torch==2.14.1 torchvision==0.29.1 torchaudio==2.11.0 --index-url $TORCH_INDEX_COMFY
  "${pip[@]}" -r "$COMFYUI_DIR/requirements.txt" -r "$COMFYUI_DIR/manager_requirements.txt"

  local entry url commit dir
  for entry in "${CUSTOM_NODES[@]}"; do
    read -r url commit <<<"$entry"
    dir=$COMFYUI_DIR/custom_nodes/$(basename "$url")
    [[ -d $dir/.git ]] || git clone --quiet "$url" "$dir"
    git -C "$dir" fetch --quiet origin
    git -C "$dir" -c advice.detachedHead=false checkout --quiet "$commit"
    [[ -f $dir/requirements.txt ]] && "${pip[@]}" -r "$dir/requirements.txt"
  done
}

install_latentsync() {
  step "LatentSync 1.6 in $LATENTSYNC_DIR"
  [[ -d $LATENTSYNC_DIR/.git ]] || git clone --quiet https://github.com/bytedance/LatentSync "$LATENTSYNC_DIR"
  git -C "$LATENTSYNC_DIR" fetch --quiet origin
  git -C "$LATENTSYNC_DIR" -c advice.detachedHead=false checkout --quiet $LATENTSYNC_COMMIT
  # Its own venv: its pins (diffusers 0.32.2, mediapipe, decord, insightface) would replace ComfyUI's packages.
  # Its torch 2.5.1 cu121 has no RTX 5090 (sm_120) kernels, so torch is the first build with them that fits
  # the rest of its pins; gradio (the demo UI) is left out.
  [[ -x $LATENTSYNC_DIR/.venv/bin/python ]] || uv venv --python 3.10 "$LATENTSYNC_DIR/.venv"
  local pip=(uv pip install --python "$LATENTSYNC_DIR/.venv/bin/python")
  "${pip[@]}" torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cu128
  "${pip[@]}" -r <(grep -v -E '^(torch|torchvision|--extra-index-url|gradio)' "$LATENTSYNC_DIR/requirements.txt")
}

download_models() {
  step "Model weights (config/models.tsv, ~85 GB)"
  local hf=(uvx --from "huggingface_hub[hf_xet]" hf download)
  local stage repo rev path dest local_dir
  while IFS=$'\t' read -r stage repo rev path dest; do
    [[ -z $stage || $stage == \#* ]] && continue
    local_dir=$COMFYUI_DIR/models/_hf/$repo
    echo "[$stage] $repo/$path"
    "${hf[@]}" "$repo" "$path" --revision "$rev" --local-dir "$local_dir" >/dev/null
    mkdir -p "$COMFYUI_DIR/models/$dest"
    ln -sfn "$local_dir/$path" "$COMFYUI_DIR/models/$dest/$(basename "$path")"
  done <"$REPO/config/models.tsv"
  local f
  for f in latentsync_unet.pt whisper/tiny.pt; do
    echo "[L] ByteDance/LatentSync-1.6/$f"
    "${hf[@]}" ByteDance/LatentSync-1.6 "$f" --revision $LATENTSYNC_HF_REV --local-dir "$LATENTSYNC_DIR/checkpoints" >/dev/null
  done
  # LatentSync's face detector (InsightFace buffalo_l) downloads itself on first use into checkpoints/auxiliary.
  # L's face crops (scripts/l_faces.py): YuNet from the OpenCV model zoo (Git LFS), checked against its hash.
  local yunet=$COMFYUI_DIR/models/detection/face_detection_yunet_2023mar.onnx
  local yunet_sha=8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4
  if ! echo "$yunet_sha  $yunet" | sha256sum -c --status 2>/dev/null; then
    echo "[L] opencv_zoo face_detection_yunet_2023mar.onnx"
    mkdir -p "$(dirname "$yunet")"
    curl -fsSL -o "$yunet" https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
    echo "$yunet_sha  $yunet" | sha256sum -c --status || { echo "YuNet hash mismatch" >&2; return 1; }
  fi
  # E's person masks in front of the S20 TV wall (scripts/e_people.py): torchvision's Mask R-CNN v2 COCO weights, in
  # the torch hub cache, where torchvision looks for them (it checks the hash prefix in the file name on download).
  local mrcnn=$HOME/.cache/torch/hub/checkpoints/maskrcnn_resnet50_fpn_v2_coco-73cbd019.pth
  local mrcnn_sha=73cbd0190fcbe3ba339921fbce2c3a0b6bb9126c9a133c85e43a2a8e060a109e
  if ! echo "$mrcnn_sha  $mrcnn" | sha256sum -c --status 2>/dev/null; then
    echo "[E] torchvision maskrcnn_resnet50_fpn_v2_coco"
    mkdir -p "$(dirname "$mrcnn")"
    curl -fsSL -o "$mrcnn" https://download.pytorch.org/models/maskrcnn_resnet50_fpn_v2_coco-73cbd019.pth
    echo "$mrcnn_sha  $mrcnn" | sha256sum -c --status || { echo "Mask R-CNN hash mismatch" >&2; return 1; }
  fi
}

check() {
  step "Checks"
  local fail=0
  ok() { printf '  ok    %s\n' "$*"; }
  bad() { printf '  FAIL  %s\n' "$*"; fail=1; }

  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | sed 's/^/  gpu   /'
  local bv; bv=$(blender --version 2>/dev/null || true)
  [[ $bv == 'Blender 5.2'* ]] && ok "${bv%%$'\n'*}" || bad "Blender 5.2"
  # Eevee needs an EGL context from the NVIDIA driver in background mode. The gpu module only initialises once
  # something renders, so render a 64 px frame first.
  local probe; probe=$(mktemp -d)
  if blender -b --factory-startup --python-expr "
import bpy, gpu
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE'
s.render.resolution_x = s.render.resolution_y = 64
s.render.filepath = '$probe/eevee.png'
bpy.ops.render.render(write_still=True)
print('GPUBACKEND', gpu.platform.renderer_get())" 2>&1 | grep 'GPUBACKEND.*NVIDIA' >/dev/null && [[ -s $probe/eevee.png ]]; then
    ok "Blender headless GPU context"
  else
    bad "Blender headless GPU context (needs EGL from the NVIDIA driver)"
  fi
  rm -rf "$probe"
  local swap; swap=$(swapon --show=SIZE --bytes --noheadings | awk '{s+=$1} END{print s+0}')
  (( swap >= SWAP_GB * 1024**3 * 95 / 100 )) && ok "swap $((swap / 1024**3)) GiB" || bad "swap below $SWAP_GB GB"
  ffmpeg -hide_banner -encoders 2>/dev/null | grep libx264 >/dev/null && ok "$(ffmpeg -version | head -1 | cut -d' ' -f1-3), libx264" || bad "ffmpeg with libx264"
  [[ $(node --version 2>/dev/null) == v$NODE_VERSION ]] && ok "node $NODE_VERSION" || bad "node $NODE_VERSION"
  (cd "$REPO" && node -e "import('puppeteer').then(async p=>{const b=await p.default.launch({headless:'shell',args:['--no-sandbox']});console.log(await b.version());await b.close()})" 2>/dev/null) \
    | sed 's/^/  ok    puppeteer → /' | grep . || bad "puppeteer launch"
  "$REPO/.venv/bin/python" -c 'import torch,whisperx,librosa; assert torch.cuda.is_available(); x=torch.ones(1,device="cuda")*2; print(f"torch {torch.__version__}, {torch.cuda.get_device_name()}, whisperx ok")' 2>/dev/null \
    | sed 's/^/  ok    project venv: /' | grep . || bad "project venv (torch CUDA, whisperx)"
  "$COMFYUI_DIR/.venv/bin/python" -c 'import torch; assert torch.cuda.is_available(); x=torch.ones(1,device="cuda")*2; print(f"torch {torch.__version__}, CUDA {torch.version.cuda}")' 2>/dev/null \
    | sed 's/^/  ok    ComfyUI venv: /' | grep . || bad "ComfyUI venv (torch CUDA)"
  (cd "$LATENTSYNC_DIR" && .venv/bin/python -c 'import torch,diffusers,insightface,mediapipe,decord; assert torch.cuda.is_available(); x=torch.ones(1,device="cuda")*2; print(f"torch {torch.__version__}, {torch.cuda.get_device_name()}")') 2>/dev/null \
    | sed 's/^/  ok    LatentSync venv: /' | grep . || bad "LatentSync venv (torch CUDA, insightface)"
  if (( MODELS )); then
    [[ -s $LATENTSYNC_DIR/checkpoints/latentsync_unet.pt ]] && ok "model LatentSync 1.6 unet" || bad "model LatentSync 1.6 unet missing"
    [[ -s $HOME/.cache/torch/hub/checkpoints/maskrcnn_resnet50_fpn_v2_coco-73cbd019.pth ]] && ok "model Mask R-CNN v2 (E people)" \
      || bad "model Mask R-CNN v2 (E people) missing"
    local stage repo rev path dest f
    while IFS=$'\t' read -r stage repo rev path dest; do
      [[ -z $stage || $stage == \#* ]] && continue
      f=$COMFYUI_DIR/models/$dest/$(basename "$path")
      [[ -s $f ]] && ok "model $dest/$(basename "$path")" || bad "model $dest/$(basename "$path") missing"
    done <"$REPO/config/models.tsv"
  fi
  return $fail
}

snapshot() {
  # Versions as installed, for the production log.
  mkdir -p "$REPO/log"
  {
    echo "# Environment snapshot, $(date -Iseconds)"
    echo "host: $(hostname), $(. /etc/os-release && echo "$PRETTY_NAME"), kernel $(uname -r)"
    echo "gpu: $(nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader)"
    echo "ram: $(free -g | awk '/Mem:/{print $2" GB"}'), swap $(swapon --show=SIZE --noheadings | head -1)"
    echo "blender: $(blender --version 2>/dev/null | head -1)"
    echo "ffmpeg: $(ffmpeg -version | head -1)"
    echo "node: $(node --version), puppeteer $(cd "$REPO" && node -p 'require("puppeteer/package.json").version')"
    echo "uv: $(uv --version)"
    echo "project venv: $("$REPO/.venv/bin/python" -c 'import sys,torch,whisperx,importlib.metadata as m; print(sys.version.split()[0], "torch", torch.__version__, "whisperx", m.version("whisperx"))')"
    echo "comfyui: $(git -C "$COMFYUI_DIR" describe --tags) ($(git -C "$COMFYUI_DIR" rev-parse --short HEAD)) at $COMFYUI_DIR"
    echo "comfyui venv: $("$COMFYUI_DIR/.venv/bin/python" -c 'import sys,torch; print(sys.version.split()[0], "torch", torch.__version__)')"
    for d in "$COMFYUI_DIR"/custom_nodes/*/; do
      [[ -d $d/.git ]] && echo "custom node: $(basename "$d") $(git -C "$d" rev-parse --short HEAD)"
    done
    echo "latentsync: $(git -C "$LATENTSYNC_DIR" rev-parse --short HEAD) at $LATENTSYNC_DIR, venv $("$LATENTSYNC_DIR/.venv/bin/python" -c 'import sys,torch; print(sys.version.split()[0], "torch", torch.__version__)')"
    echo "models: config/models.tsv (pinned revisions); LatentSync-1.6 at $LATENTSYNC_HF_REV"
  } >"$REPO/log/environment.txt"
  echo "wrote log/environment.txt"
}

if (( ! CHECK_ONLY )); then
  install_system
  ensure_swap
  install_project
  install_comfyui
  install_latentsync
  (( MODELS )) && download_models
fi
check
snapshot
