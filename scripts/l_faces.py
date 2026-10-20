"""L: find the singer's face in every frame of each L shot's approved V take (YuNet, OpenCV's face detector).

l_batch.py builds each clip's mask from these boxes. Runs in ComfyUI's venv, which has OpenCV; the model is
~/ComfyUI/models/detection/face_detection_yunet_2023mar.onnx (scripts/setup_env.sh).
Writes takes/l/<shot>/faces.json: per frame [x, y, w, h, score] of the most confident face, or null.

Usage: ~/ComfyUI/.venv/bin/python scripts/l_faces.py [shot ...]
"""
import json
import sys
from pathlib import Path

import cv2

MODEL = str(Path.home() / "ComfyUI/models/detection/face_detection_yunet_2023mar.onnx")
CFG = json.load(open("config/l.json"))
PICKS = json.load(open("config/v_picks.json"))["picks"]


def faces(video):
    cap = cv2.VideoCapture(str(video))
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    det = cv2.FaceDetectorYN.create(MODEL, "", (w, h), 0.6)
    out = []
    while True:
        ok, frame = cap.read()
        if not ok:
            return out
        _, found = det.detect(frame)
        if found is None:
            out.append(None)
        else:
            best = max(found, key=lambda f: f[14])
            out.append([round(float(v), 1) for v in best[:4]] + [round(float(best[14]), 3)])


def main():
    for shot in sys.argv[1:] or list(CFG["shots"]):
        if shot in CFG.get("extra", {}):  # an extra shot: its source clip (l_batch.py --prepare)
            take = Path("takes/l") / shot / "source.mp4"
        else:
            pick = PICKS[shot] if isinstance(PICKS[shot], str) else PICKS[shot]["file"]
            take = Path("takes/v") / shot / pick
        boxes = faces(take)
        d = Path("takes/l") / shot
        d.mkdir(parents=True, exist_ok=True)
        json.dump({"take": str(take), "faces": boxes}, open(d / "faces.json", "w"))
        found = sum(b is not None for b in boxes)
        print(f"{shot}: face in {found} of {len(boxes)} frames")


if __name__ == "__main__":
    main()
