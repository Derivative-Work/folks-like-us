"""O: track each text surface through its shot's approved take (config/o.json "surfaces").

The Blender anchors only seed this: V follows the layout loosely (a hand-held mug moves with the hand, the S20 TV
wall is larger than the layout's), so each surface's quad is placed by hand on one frame of the take ("frame",
"quad": TL, TR, BR, BL in take pixels) and tracked from there in both directions. Each step tracks corner features
(Lucas-Kanade, forward-backward checked) inside the quad's bounding box padded by "pad" px, or inside "region" if
given (a hand-held mug tracks with the hand around it), and fits "model": "similarity" (default; stable on small
surfaces with few features), "affine" or "homography". Quads are smoothed over "smooth" frames. A static camera
("model": "static") holds the quad. Where tracking fails (S18's bill as the room goes dark), "keys" places the quad
by hand on a few frames ({frame: quad}) and interpolates linearly between them.

Writes takes/o/tracks/<shot>__<name>.json: {"take", "size", "quads": [[[x, y] x4] per frame]}, and a review sheet
takes/o/tracks/<shot>__<name>.png (the quad drawn on the first, middle and last frames).

Runs in ComfyUI's venv, which has OpenCV: ~/ComfyUI/.venv/bin/python scripts/o_track.py [shot[:name] ...]
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

CFG = json.load(open("config/o.json"))
OUT = Path("takes/o/tracks")


def frames(take):
    cap = cv2.VideoCapture(take)
    out = []
    while True:
        ok, f = cap.read()
        if not ok:
            return out
        out.append(f)


def features(gray, box):
    x0, y0, x1, y1 = box
    m = np.zeros_like(gray)
    m[max(0, y0):y1, max(0, x0):x1] = 255
    p = cv2.goodFeaturesToTrack(gray, 200, 0.01, 3, mask=m, blockSize=5)
    return p if p is not None else np.zeros((0, 1, 2), np.float32)


def step(g0, g1, box, model):
    """The transform taking frame g0 to g1, from features inside box (a 2x3 or 3x3 matrix, or None)."""
    p0 = features(g0, box)
    if len(p0) < 3:
        return None
    lk = dict(winSize=(21, 21), maxLevel=3, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01))
    p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g1, p0, None, **lk)
    pb, stb, _ = cv2.calcOpticalFlowPyrLK(g1, g0, p1, None, **lk)
    good = (st[:, 0] == 1) & (stb[:, 0] == 1) & (np.linalg.norm(p0 - pb, axis=2)[:, 0] < 1.0)
    a, b = p0[good], p1[good]
    if model == "homography" and len(a) >= 8:
        H, _ = cv2.findHomography(a, b, cv2.RANSAC, 2.0)
        return H
    if len(a) < 3:
        return None
    fit = cv2.estimateAffine2D if model == "affine" else cv2.estimateAffinePartial2D
    M, _ = fit(a, b, method=cv2.RANSAC, ransacReprojThreshold=2.0)
    return M


def apply(M, quad):
    q = np.asarray(quad, np.float32).reshape(-1, 1, 2)
    return (cv2.perspectiveTransform(q, M) if M.shape == (3, 3) else cv2.transform(q, M)).reshape(-1, 2)


def bbox(quad, pad, size):
    q = np.asarray(quad)
    w, h = size
    return (int(max(0, q[:, 0].min() - pad)), int(max(0, q[:, 1].min() - pad)),
            int(min(w, q[:, 0].max() + pad)), int(min(h, q[:, 1].max() + pad)))


def track(s):
    fr = frames(s["take"])
    h, w = fr[0].shape[:2]
    if "keys" in s:
        keys = sorted((int(k), np.asarray(v, np.float32)) for k, v in s["keys"].items())
        out = []
        for i in range(len(fr)):
            a = max((k for k in keys if k[0] <= i), key=lambda k: k[0], default=keys[0])
            b = min((k for k in keys if k[0] >= i), key=lambda k: k[0], default=keys[-1])
            u = 0 if b[0] == a[0] else (i - a[0]) / (b[0] - a[0])
            out.append((1 - u) * a[1] + u * b[1])
        return fr, np.stack(out), (w, h)
    gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]
    n, r = len(fr), s.get("frame", 0)
    quads = [None] * n
    quads[r] = np.asarray(s["quad"], np.float32)
    model = s.get("model", "similarity")
    region = s.get("region")  # [x0, y0, x1, y1] on the reference frame, moved with the quad
    for direction in (1, -1):
        i = r
        while 0 <= i + direction < n:
            j = i + direction
            if model == "static":
                quads[j] = quads[i]
            else:
                if region:
                    off = quads[i].mean(0) - quads[r].mean(0)
                    box = (int(region[0] + off[0]), int(region[1] + off[1]), int(region[2] + off[0]),
                           int(region[3] + off[1]))
                else:
                    box = bbox(quads[i], s.get("pad", 12), (w, h))
                M = step(gray[i], gray[j], box, model)
                quads[j] = apply(M, quads[i]) if M is not None else quads[i]
            i = j
    q = np.stack(quads)
    k = s.get("smooth", 5)
    if k > 1:
        pad = np.pad(q, ((k // 2, k // 2), (0, 0), (0, 0)), mode="edge")
        q = np.stack([pad[i:i + n] for i in range(k)]).mean(0)
    return fr, q, (w, h)


def review(fr, q, path):
    tiles = []
    for i in (0, len(fr) // 2, len(fr) - 1):
        f = fr[i].copy()
        cv2.polylines(f, [q[i].astype(np.int32).reshape(-1, 1, 2)], True, (0, 0, 255), 2)
        tiles.append(f)
    cv2.imwrite(str(path), cv2.resize(np.hstack(tiles), None, fx=0.5, fy=0.5))


def main():
    want = sys.argv[1:]
    OUT.mkdir(parents=True, exist_ok=True)
    for s in CFG["surfaces"]:
        key = f"{s['shot']}:{s['name']}"
        if want and s["shot"] not in want and key not in want:
            continue
        fr, q, size = track(s)
        base = OUT / f"{s['shot']}__{s['name']}"
        json.dump({"take": s["take"], "size": size, "quads": np.round(q, 2).tolist()}, open(f"{base}.json", "w"))
        review(fr, q, f"{base}.png")
        drift = float(np.linalg.norm(q[-1].mean(0) - q[0].mean(0)))
        print(f"{key}: {len(fr)} frames, centre moved {drift:.1f} px")


if __name__ == "__main__":
    main()
