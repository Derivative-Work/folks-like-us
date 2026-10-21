"""Render B shots from scenes/town.blend: plates and guide passes for V, and stills for the contact sheet.

For each shot in config/shots_b.json: apply its section's continuity (config/continuity.json) and overrides, show
only its cast, place the camera (with its move over the shot), then render each frame to
  <out>/<shot>/beauty/NNNNN.png   tonemapped (AgX), the look reference
  <out>/<shot>/depth/NNNNN.png    16-bit relative inverse depth: near = white, the shot's 'far' and beyond = black
  <out>/<shot>/normal/NNNNN.png   camera-space normals, RGB = (x, y, z) * 0.5 + 0.5
  <out>/<shot>/mask/NNNNN.png     the building (AOV building_mask): white
  <out>/<shot>/exr/NNNNN.exr      all passes, scene-linear (multilayer)
and writes <out>/<shot>/shot.json (camera, frames, continuity) and <out>/<shot>/anchors.json (each text surface in
frame: its four corners per frame, in normalised image coordinates with y down, for O's corner pins, and whether
something hides its centre).

Usage:
  blender -b scenes/town.blend --python scripts/blender/render_shot.py -- <shot|all> [...] [--still]
          [--frames A:B] [--res WxH] [--samples N] [--out DIR]
--still renders the shot's middle frame only; --first its first frame (the keyframe layout for V). --res is the 16:9 size; vertical shots swap it.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
import OpenImageIO as oiio
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

REPO = Path(bpy.data.filepath).resolve().parents[1]
SHOTS = json.load(open(REPO / "config/shots_b.json"))["shots"]
CONT = json.load(open(REPO / "config/continuity.json"))
TIMES = json.load(open(REPO / "timing/shot_times.json"))["shots"]
FPS = 24
CAST_ROLES = {"singer", "grandma", "kid", "patron", "dog"}
HIDDEN_PROPS = {"leash", "kite", "kite_string", "mug_table", "txt_mug_table", "mug_rail", "txt_mug_rail", "pie",
                "pie_tin"}


# ---------------------------------------------------------------- helpers

def descendants(o):
    out = [o]
    for c in o.children:
        out += descendants(c)
    return out


def set_visible(o, visible):
    for d in descendants(o):
        d.hide_render = not visible
        d.hide_viewport = not visible


def ray_dir():
    a = math.radians(bpy.context.scene["ray_azimuth"])
    return Vector((math.sin(a), math.cos(a), 0))


def nearest_hall(p, stage):
    min_d = bpy.context.scene["stage_min_d"][stage]
    halls = [d for d in bpy.context.scene["hall_d"] if d >= min_d]
    pts = [ray_dir() * d for d in halls]
    return min(pts, key=lambda q: (q - p).length)


def yaw_towards(src, dst):
    v = dst - src
    return math.atan2(-v.x, v.y)  # rotation about Z that turns +Y towards v


def param(values, key, t):
    """values[key], with [start, end] pairs interpolated at t in [0, 1]. Dotted keys reach into dicts."""
    v = values
    for k in key.split("."):
        v = v[k]
    if isinstance(v, list):
        return v[0] + (v[1] - v[0]) * t
    return v


def continuity(shot):
    vals = json.loads(json.dumps(CONT["sections"][shot["section"]]))
    for k, v in shot.get("set", {}).items():
        d = vals
        parts = k.split(".")
        for p in parts[:-1]:
            d = d[p]
        d[parts[-1]] = v
    return vals


# ---------------------------------------------------------------- applying a shot

def apply_world(vals, t, frame):
    """Set stage, lights and gauge for time t in [0, 1] of the shot; keyframe the animated values at frame."""
    sc = bpy.context.scene
    E = CONT["energies"]
    stage = vals["stage"]
    min_d = sc["stage_min_d"][stage]
    for c in bpy.data.collections:
        if c.name.startswith("Hall_"):
            c.hide_render = c["d"] < min_d
    bpy.data.collections["Cranes"].hide_render = not vals["cranes"]
    flood = param(vals, "flood", t)
    led = param(vals, "led", t)
    bpy.data.materials["flood_lamp"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = \
        flood * E["flood_lamp_emit"]
    bpy.data.materials["hall_led"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = \
        led * E["led_emit"]
    for o in bpy.data.objects:
        if o.get("flood"):
            o.data.energy = flood * E["flood_spot"]
            o.data.keyframe_insert("energy", frame=frame)
        if o.get("practical"):
            o.data.energy = o.get("base_energy", o.data.energy) * param(vals["practicals"], o["practical"], t)
            o.data.keyframe_insert("energy", frame=frame)
    for name in ("flood_lamp", "hall_led"):
        bpy.data.materials[name].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].keyframe_insert(
            "default_value", frame=frame)
    wash = bpy.data.objects["building_wash"].data
    wash.energy = param(vals, "building_wash", t) * E["building_wash"]
    wash.keyframe_insert("energy", frame=frame)
    sun = bpy.data.objects["Sun"].data
    sun.energy = param(vals, "sun", t) * E["sun"]
    sun.keyframe_insert("energy", frame=frame)
    bg = sc.world.node_tree.nodes["Background"].inputs["Strength"]
    bg.default_value = param(vals, "sky", t) * E["sky"]
    bg.keyframe_insert("default_value", frame=frame)
    g = bpy.data.objects["gauge_fill"]
    g.scale.z = max(0.001, param(vals, "gauge", t))


def remember_base_energies():
    for o in bpy.data.objects:
        if o.get("practical") and "base_energy" not in o:
            o["base_energy"] = o.data.energy


def apply_cast(shot, vals, cam_loc, f0, f1):
    cast = shot.get("cast", {})
    for o in bpy.data.objects:
        role = o.get("role")
        if o.parent is None and (role in CAST_ROLES):
            set_visible(o, False)
        if o.name in HIDDEN_PROPS:
            set_visible(o, False)
    for o in bpy.data.objects:  # cows: shown only when cast, always facing the nearest hall
        if o.get("faces") == "building":
            set_visible(o, "cows" in cast)
            if vals["cows_face_building"]:
                o.rotation_euler.z = yaw_towards(o.location, nearest_hall(o.location, vals["stage"]))
    for name, spec in cast.items():
        if name == "cows":
            continue
        targets = [o for o in bpy.data.objects if o.get("role") == "patron" and o.parent is None] \
            if name == "patrons" else [bpy.data.objects[name]]
        if f"txt_{name}" in bpy.data.objects:  # a cast prop brings its text surface (mug_rail -> txt_mug_rail)
            set_visible(bpy.data.objects[f"txt_{name}"], True)
        for o in targets:
            set_visible(o, True)
            if "loc" in spec:
                o.location = spec["loc"]
                o.keyframe_insert("location", frame=f0)
            if "loc_end" in spec:
                o.location = spec["loc_end"]
                o.keyframe_insert("location", frame=f1)
                o.location = spec["loc"]
            face = spec.get("face")
            if face == "camera":
                o.rotation_euler.z = yaw_towards(o.location, Vector(cam_loc))
            elif face == "building":
                o.rotation_euler.z = yaw_towards(o.location, nearest_hall(o.location, vals["stage"]))
            elif "yaw" in spec:
                o.rotation_euler.z = math.radians(spec["yaw"])


def make_camera(shot, f0, f1):
    sc = bpy.context.scene
    for o in [o for o in bpy.data.objects if o.name.startswith("ShotCam")]:
        bpy.data.objects.remove(o)
    cd = bpy.data.cameras.new("ShotCam")
    cd.lens = shot["lens"]
    cd.sensor_width = 36.0
    cd.sensor_fit = "AUTO"
    cd.clip_start = 0.05
    cd.clip_end = 8000
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = shot["fstop"]
    cam = bpy.data.objects.new("ShotCam", cd)
    sc.collection.objects.link(cam)
    aim = bpy.data.objects.new("ShotCamAim", None)
    sc.collection.objects.link(aim)
    con = cam.constraints.new("TRACK_TO")
    con.target = aim
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    sc.camera = cam
    c0, t0 = Vector(shot["cam"]), Vector(shot["target"])
    move = shot.get("move", {})
    c1, t1 = c0.copy(), t0.copy()
    if "push" in move:
        c1 = c0 + (t0 - c0) * move["push"]
    if "dolly" in move:
        c1, t1 = c0 + Vector(move["dolly"]), t0 + Vector(move["dolly"])
    if move.get("pan"):
        t1 = Vector(shot["target_end"])
    focus = bpy.data.objects.get(shot.get("focus", ""))
    for f, c, t in ((f0, c0, t0), (f1, c1, t1)):
        cam.location, aim.location = c, t
        cam.keyframe_insert("location", frame=f)
        aim.keyframe_insert("location", frame=f)
        fp = (focus.matrix_world.translation + Vector((0, 0, 1.4 if focus.get("role") else 0.05))) if focus else t
        cd.dof.focus_distance = (fp - c).length
        cd.dof.keyframe_insert("focus_distance", frame=f)
    for fc in list(_fcurves(cam)) + list(_fcurves(aim)) + list(_fcurves(cd)):
        for kp in fc.keyframe_points:
            kp.interpolation = "SINE"  # ease in and out: slow push-ins (style spec)
    return cam


def _fcurves(idblock):
    ad = idblock.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if hasattr(act, "fcurves"):
        return act.fcurves
    out = []  # slotted actions (Blender 4.4+): curves live in layers/strips/channelbags
    for layer in act.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                out += list(cb.fcurves)
    return out


# ---------------------------------------------------------------- outputs

def text_anchors(cam, frames):
    sc = bpy.context.scene
    out = {}
    for o in bpy.data.objects:
        if not o.name.startswith("txt_") or o.hide_render:
            continue
        per = {}
        for f in frames:
            sc.frame_set(f)
            mw = o.matrix_world
            pts = [world_to_camera_view(sc, cam, mw @ v.co) for v in o.data.vertices]
            if any(p.z > 0 and 0 <= p.x <= 1 and 0 <= p.y <= 1 for p in pts):
                per[f] = {"corners": [[round(p.x, 5), round(1 - p.y, 5)] for p in pts],
                          "occluded": occluded(o, cam)}
        if per:
            out[o["text_surface"]] = per
    return out


def occluded(o, cam):
    """Whether something else hides the surface's centre from the camera (one ray; partial cover isn't
    resolved: O masks with the depth pass for that)."""
    dg = bpy.context.evaluated_depsgraph_get()
    centre = o.matrix_world @ (sum((v.co for v in o.data.vertices), Vector()) / len(o.data.vertices))
    origin = cam.matrix_world.translation
    d = centre - origin
    hit, loc, _, _, obj, _ = bpy.context.scene.ray_cast(dg, origin, d.normalized(), distance=d.length - 0.01)
    return bool(hit and obj is not None and obj.name != o.name)


def split_exr(exr, outdir, frame, far):
    inp = oiio.ImageInput.open(str(exr))
    names = []
    sub = 0
    layers = {}
    while inp.seek_subimage(sub, 0):
        spec = inp.spec()
        px = inp.read_image(sub, 0, 0, spec.nchannels, oiio.FLOAT)
        for i, ch in enumerate(spec.channelnames):
            layers[ch] = px[:, :, i]
        names += list(spec.channelnames)
        sub += 1
    inp.close()

    def find(*cands):
        for c in cands:
            for n in layers:
                if n.endswith(c):
                    return layers[n]
        raise KeyError(f"{cands} not in {sorted(layers)[:40]}")

    # Relative inverse depth (MiDaS-style, what depth-guided video models expect): 1/Z, from the shot's far
    # limit (0) to the nearest 1% of pixels (1). The sky and anything past 'far' are 0.
    z = find("Depth.Z")
    inv = 1.0 / np.maximum(z, 0.05)
    lo, hi = 1.0 / far, np.percentile(inv, 99)
    depth = np.clip((inv - lo) / max(hi - lo, 1e-6), 0, 1)
    write_png(outdir / "depth" / f"{frame:05d}.png", depth, 16)
    mask = np.clip(find("building_mask.Value", "building_mask.V", "building_mask.X", "building_mask"), 0, 1)
    write_png(outdir / "mask" / f"{frame:05d}.png", mask, 8)
    n = np.stack([find("Normal.X"), find("Normal.Y"), find("Normal.Z")], -1)
    cam = bpy.context.scene.camera
    rot = np.array(cam.matrix_world.to_3x3().inverted())
    nc = n @ rot.T
    write_png(outdir / "normal" / f"{frame:05d}.png", np.clip(nc * 0.5 + 0.5, 0, 1), 8)


def write_png(path, arr, bits):
    path.parent.mkdir(parents=True, exist_ok=True)
    a = arr.astype(np.float32)
    if a.ndim == 2:
        a = a[:, :, None]  # OIIO needs an explicit channel axis
    a = np.ascontiguousarray(a)
    ch = a.shape[2]
    spec = oiio.ImageSpec(a.shape[1], a.shape[0], ch, oiio.UINT16 if bits == 16 else oiio.UINT8)
    out = oiio.ImageOutput.create(str(path))
    out.open(str(path), spec)
    out.write_image(a)
    out.close()


BUILT = {}


def restore_built():
    """Put every object back where build_town.py left it: clearing animation keeps the last keyed values, so a
    stand-in moved by one shot (S19's singer in the kitchen) would otherwise stay there for the next."""
    for o in bpy.data.objects:
        if o.name not in BUILT:
            BUILT[o.name] = (o.location.copy(), o.rotation_euler.copy(), o.scale.copy())
        o.location, o.rotation_euler, o.scale = (v.copy() for v in BUILT[o.name])


def render_shot(sid, args):
    shot = SHOTS[sid]
    times = TIMES[shot["time"]]
    s0, s1 = times["start_frame"], times["end_frame"]
    if "part" in shot:
        k, n = shot["part"]
        span = (s1 - s0) / n
        s0, s1 = round(times["start_frame"] + k * span), round(times["start_frame"] + (k + 1) * span)
    if "span" in shot:  # lengthened in the edit (config/edit.json "cuts")
        s0, s1 = shot["span"]
    if args.frames:
        a, b = args.frames.split(":")
        frames = list(range(int(a), int(b)))
    elif args.first:
        frames = [s0]  # the frame V starts from: its keyframe is made from this one
    elif args.still:
        frames = [(s0 + s1) // 2]
    else:
        frames = list(range(s0, s1))
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = s0, max(s0, s1 - 1)
    w, h = (int(x) for x in args.res.split("x"))
    if shot.get("vertical"):
        w, h = h, w
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
    sc.eevee.taa_render_samples = args.samples
    sc.world.mist_settings.start = 0.0
    sc.world.mist_settings.depth = shot.get("far", 300)
    vals = continuity(shot)
    remember_base_energies()
    for o in bpy.data.objects:  # clear animation left by a previous shot in this session
        o.animation_data_clear()
        if o.data is not None and hasattr(o.data, "animation_data_clear"):
            o.data.animation_data_clear()
    restore_built()
    for m in ("flood_lamp", "hall_led"):
        bpy.data.materials[m].node_tree.animation_data_clear()
    sc.world.node_tree.animation_data_clear()
    apply_world(vals, 0.0, s0)
    apply_world(vals, 1.0, max(s0 + 1, s1))
    cam = make_camera(shot, s0, max(s0 + 1, s1))
    apply_cast(shot, vals, shot["cam"], s0, max(s0 + 1, s1))
    out = Path(args.out) / sid
    for sub in ("beauty", "exr"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    for f in frames:
        sc.frame_set(f)
        bpy.ops.render.render(write_still=False)
        img = bpy.data.images["Render Result"]
        sc.render.image_settings.media_type = "MULTI_LAYER_IMAGE"  # Blender 5: multilayer EXR is a media type
        sc.render.image_settings.file_format = "OPEN_EXR_MULTILAYER"
        sc.render.image_settings.color_depth = "32"
        sc.render.image_settings.exr_codec = "ZIP"
        exr = out / "exr" / f"{f:05d}.exr"
        img.save_render(str(exr), scene=sc)
        sc.render.image_settings.media_type = "IMAGE"
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_depth = "8"
        img.save_render(str(out / "beauty" / f"{f:05d}.png"), scene=sc)
        split_exr(exr, out, f, shot.get("far", 300))
    anchors = text_anchors(cam, frames)
    json.dump(anchors, open(out / "anchors.json", "w"))
    meta = {"shot": sid, "what": shot.get("what"), "section": shot["section"], "stage": vals["stage"],
            "time": shot["time"], "frames_shot": [s0, s1], "frames_rendered": [frames[0], frames[-1] + 1],
            "resolution": [w, h], "samples": args.samples, "camera": {k: shot.get(k) for k in
                                                                       ("cam", "target", "target_end", "lens", "fstop",
                                                                        "focus", "move")},
            "continuity": vals, "cast": shot.get("cast", {}),
            "text_surfaces": sorted(k for k, v in anchors.items() if any(not x["occluded"] for x in v.values())),
            "blender": bpy.app.version_string}
    json.dump(meta, open(out / "shot.json", "w"), indent=1, ensure_ascii=False)
    print(f"{sid}: frames {frames[0]}-{frames[-1]} -> {out}")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("shots", nargs="+")
    ap.add_argument("--still", action="store_true")
    ap.add_argument("--first", action="store_true")
    ap.add_argument("--frames")
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--samples", type=int, default=64)
    ap.add_argument("--out", default=str(REPO / "renders/b/plates"))
    args = ap.parse_args(argv)
    shots = list(SHOTS) if args.shots == ["all"] else args.shots
    for sid in shots:
        render_shot(sid, args)


if __name__ == "__main__":
    main()
