"""E: the diners in front of S20's TV wall, as per-frame person masks (torchvision Mask R-CNN v2, COCO "person").

e_edit.py fills each TV's tracked quad with its content except where a person stands in front. A colour key on the
screens' dark pixels could not tell dark hair from a dark screen, and screen glare left holes (log/decisions.md).
Runs in ComfyUI's venv, which has torch and torchvision; the weights download to the torch hub cache
(scripts/setup_env.sh).
Writes takes/e/people/S20/NNNNN.png (take size, 0-255 person probability, frame = the take's frame).

Usage: ~/ComfyUI/.venv/bin/python scripts/e_people.py
"""
import json
import subprocess
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torchvision.models.detection import MaskRCNN_ResNet50_FPN_V2_Weights, maskrcnn_resnet50_fpn_v2

PICKS = json.load(open("config/v_picks.json"))["picks"]
OUT = Path("takes/e/people/S20")
PERSON, MIN_SCORE = 1, 0.5


def frames(path):
    w, h = (int(x) for x in subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0",
         path], capture_output=True, text=True, check=True).stdout.strip().split(","))
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


@torch.inference_mode()
def main():
    p = PICKS["S20"]
    take = f"takes/v/S20/{p if isinstance(p, str) else p['file']}"
    weights = MaskRCNN_ResNet50_FPN_V2_Weights.COCO_V1
    model = maskrcnn_resnet50_fpn_v2(weights=weights).eval().cuda()
    OUT.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(frames(take)):
        x = torch.from_numpy(f.copy()).permute(2, 0, 1).float().div(255).cuda()
        r = model([x])[0]
        keep = (r["labels"] == PERSON) & (r["scores"] >= MIN_SCORE)
        m = r["masks"][keep, 0].amax(0) if keep.any() else torch.zeros(f.shape[:2], device="cuda")
        Image.fromarray((m.cpu().numpy() * 255).astype(np.uint8)).save(OUT / f"{i:05d}.png")
    print(f"S20: {i + 1} frames of person masks in {OUT}")


if __name__ == "__main__":
    main()
