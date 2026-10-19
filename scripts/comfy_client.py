"""Minimal ComfyUI API client: upload images, queue an API-format graph, wait, download the outputs.

The server runs separately: ~/ComfyUI/.venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port 8188
"""
import json
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

HOST = "http://127.0.0.1:8188"


def _req(path, data=None, headers=None):
    req = urllib.request.Request(HOST + path, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def upload_image(path):
    """Upload a local image to ComfyUI's input folder; returns the name LoadImage uses."""
    path = Path(path)
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{path.name}\"\r\n"
            f"Content-Type: image/png\r\n\r\n").encode() + path.read_bytes() + \
        (f"\r\n--{boundary}\r\nContent-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n"
         f"--{boundary}--\r\n").encode()
    out = json.loads(_req("/upload/image", body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}))
    return out["name"]


def run(graph, poll=1.0, timeout=3600):
    """Queue a graph and wait for it. Returns (outputs, seconds)."""
    t0 = time.time()
    body = json.dumps({"prompt": graph, "client_id": "folks-like-us"}).encode()
    resp = json.loads(_req("/prompt", body, {"Content-Type": "application/json"}))
    if resp.get("node_errors"):
        raise RuntimeError(f"node errors: {resp['node_errors']}")
    pid = resp["prompt_id"]
    while time.time() - t0 < timeout:
        hist = json.loads(_req(f"/history/{pid}"))
        if pid in hist:
            h = hist[pid]
            status = h.get("status", {})
            if status.get("status_str") == "error":
                raise RuntimeError(f"generation failed: {json.dumps(status.get('messages'))[:2000]}")
            if status.get("completed"):
                return h["outputs"], time.time() - t0
        time.sleep(poll)
    raise TimeoutError(f"prompt {pid} not done after {timeout} s")


def download(image, dest):
    q = urllib.parse.urlencode({"filename": image["filename"], "subfolder": image["subfolder"],
                                "type": image["type"]})
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(_req(f"/view?{q}"))
    return dest


def free():
    """Unload models and free memory between stages (brief: one model at a time)."""
    _req("/free", json.dumps({"unload_models": True, "free_memory": True}).encode(),
         {"Content-Type": "application/json"})
