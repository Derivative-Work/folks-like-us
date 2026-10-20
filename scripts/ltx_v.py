"""V: LTX-2.3 IC-LoRA Union Control over a Blender depth pass, from ComfyUI's video_ltx2_3_ic_lora template.

The template (comfy/templates/, converted to API format in comfy/api/ by scripts/comfy_ui_to_api.mjs) estimates
depth from a source video with MoGe. Here the Blender depth pass replaces that estimate, so the generated video
follows the set kit's geometry exactly: the MoGe group and the source video are removed and LTXVAddGuide takes the
depth frames. The first frame (LTXVImgToVideoInplace) and the prompt are the shot's.
While it runs, GPU memory, RAM and swap are sampled once a second; peaks are printed and returned.

Usage: .venv/bin/python scripts/ltx_v.py <control.mp4> <first_frame.png> <out.mp4> --prompt "..." [--seed N]
       [--control depth|moge]
       [--width 1280 --height 704]
"""
import argparse
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import comfy_client as cc  # noqa: E402

TEMPLATE = Path("comfy/api/video_ltx2_3_ic_lora.api.json")


# The template's negative prompt describes its own example (it bans smiling and eye contact, which our singer does).
NEGATIVE = ("blurry, out of focus, overexposed, low contrast, washed out colors, flickering, distorted proportions, "
            "deformed face, deformed hands, extra fingers, extra limbs, morphing, melting, warped geometry, "
            "cartoonish rendering, 3D CGI look, video game graphics, plastic skin, text, letters, watermark, logo, "
            "jittery movement, camera shake, sudden cuts")


def build(control_name, image_name, prompt, seed, width, height, prefix, control="depth"):
    """control="depth": the control video is a depth pass, fed to LTXVAddGuide directly (the MoGe group is dropped).
    control="moge": the control video is the Blender beauty pass, and the template's MoGe group estimates its depth."""
    g = json.loads(TEMPLATE.read_text())
    if control == "depth":
        for k in [k for k in g if k.startswith("697:") or k in ("199", "692")]:
            del g[k]
        g["ctl_load"] = {"class_type": "LoadVideo", "inputs": {"file": control_name}}
        g["ctl_frames"] = {"class_type": "GetVideoComponents", "inputs": {"video": ["ctl_load", 0]}}
        g["129:115"]["inputs"]["image"] = ["ctl_frames", 0]
        g["129:694"]["inputs"]["image"] = ["ctl_frames", 0]
    else:
        g["199"]["inputs"]["file"] = control_name
        g["692"]["inputs"]["duration"] = 60
    g["200"]["inputs"]["image"] = image_name
    g["129:212"]["inputs"]["value"] = False          # use our prompt, not the Gemma prompt generator
    g["129:211"]["inputs"]["on_false"] = prompt
    g["129:112"]["inputs"]["text"] = NEGATIVE
    g["129:114"]["inputs"]["value"] = 24              # frame rate (template: 25); the edit is 24 fps
    g["129:704"]["inputs"]["seed"] = seed
    g["129:113"]["inputs"]["value"] = width
    g["129:98"]["inputs"]["value"] = height
    g["68"]["inputs"]["filename_prefix"] = prefix
    return g


class Monitor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.stop = False
        self.peak = {"gpu_mib": 0, "ram_used_gib": 0.0, "swap_used_gib": 0.0}

    def run(self):
        while not self.stop:
            gpu = int(subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                     capture_output=True, text=True).stdout.split()[0])
            mem = {l.split(":")[0]: int(l.split()[1]) for l in open("/proc/meminfo")}
            ram = (mem["MemTotal"] - mem["MemAvailable"]) / 2 ** 20
            swap = (mem["SwapTotal"] - mem["SwapFree"]) / 2 ** 20
            self.peak = {"gpu_mib": max(self.peak["gpu_mib"], gpu),
                         "ram_used_gib": round(max(self.peak["ram_used_gib"], ram), 1),
                         "swap_used_gib": round(max(self.peak["swap_used_gib"], swap), 1)}
            time.sleep(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("control_video", help="depth video (--control depth) or beauty video (--control moge)")
    ap.add_argument("first")
    ap.add_argument("out")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=704)
    ap.add_argument("--control", choices=["depth", "moge"], default="depth")
    a = ap.parse_args()
    control_name = cc.upload_image(a.control_video)
    image_name = cc.upload_image(a.first)
    g = build(control_name, image_name, a.prompt, a.seed, a.width, a.height, f"folks/v_{Path(a.out).stem}", a.control)
    mon = Monitor()
    mon.start()
    outputs, secs = cc.run(g, timeout=7200)
    mon.stop = True
    # The take is SaveVideo (node 68); other nodes also return videos (the control's preview), so never take "the first".
    vid = next(v for k, vs in outputs["68"].items() if k in ("images", "videos", "gifs") for v in vs)
    cc.download(vid, a.out)
    print(json.dumps({"out": a.out, "seconds": round(secs, 1), **mon.peak}))


if __name__ == "__main__":
    main()
