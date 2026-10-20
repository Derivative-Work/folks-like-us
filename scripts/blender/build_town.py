"""Pre-production step 5 [B]: build the one Blender town (scenes/town.blend) from code.

World: metres, Z up, +Y north. Morning golden hour, sun low in the east.
- Farm: a one-storey farmhouse at the origin, its porch on the south side (the master set); the kitchen inside its
  north-east corner, window facing north; the yard to the south; cornfield, pasture, water tower and power lines.
- The building is a data-centre campus: identical gray, windowless halls along one ray from the farm (RAY_AZIMUTH,
  degrees east of north). Each stage adds halls nearer the farm (STAGE_MIN_D); render_shot.py hides the halls a
  stage hasn't reached. Every hall material writes the AOV "building_mask" = 1 (S33 keeps the building sharp).
- Main street, north of the farm beside the campus: diner (window facing the campus, TV wall), church with a
  marquee, yard signs.
- Text surfaces (collection "TextSurfaces", objects named txt_*) are blank planes; O composites text onto them using
  the screen corners render_shot.py exports. No legible text is modelled (brief).
- Characters are mannequin stand-ins: they give V's depth and normal guides the right shapes to generate over.

Usage: blender -b --factory-startup --python scripts/blender/build_town.py  ->  scenes/town.blend
"""
import math
import random
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "scenes" / "town.blend"
RAY_AZIMUTH = 30.0
HALL = dict(length=130.0, width=120.0, height=45.0, spacing=150.0)
HALL_D = [110 + HALL["spacing"] * i for i in range(20)]           # hall centres along the ray: 110 m to 2960 m
STAGE_MIN_D = {"B1": 2900.0, "B2": 1300.0, "B3": 250.0, "B4": 100.0}  # halls with d >= this exist at the stage
CRANE_D = [1300.0, 1450.0, 1600.0]                                 # B1's construction site (where B2 builds)
SEED = 7

random.seed(SEED)


def ray(d, side=0.0, z=0.0):
    """Point d metres along the campus ray, side metres to its right (east of the ray)."""
    a = math.radians(RAY_AZIMUTH)
    u = Vector((math.sin(a), math.cos(a), 0))
    r = Vector((math.cos(a), -math.sin(a), 0))
    return u * d + r * side + Vector((0, 0, z))


def ray_yaw():
    return -math.radians(RAY_AZIMUTH)  # rotation about Z that turns +Y onto the ray


# ---------------------------------------------------------------- scene, collections, materials

def reset():
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights, bpy.data.cameras):
        for b in list(block):
            block.remove(b)


COLLS = {}


def coll(name, parent=None):
    if name not in COLLS:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
        COLLS[name] = c
    return COLLS[name]


MATS = {}


def mat(name, color, rough=0.6, metal=0.0, emit=None, emit_strength=0.0, mask=False):
    """Principled material. mask=True adds an AOV Output 'building_mask' = 1."""
    key = name
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit:
        bsdf.inputs["Emission Color"].default_value = (*emit, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    if mask:
        aov = nt.nodes.new("ShaderNodeOutputAOV")
        aov.aov_name = "building_mask"
        aov.inputs["Value"].default_value = 1.0
    m.diffuse_color = (*color, 1.0)
    MATS[key] = m
    return m


def obj_from_bmesh(name, bm, material, collection, loc=(0, 0, 0), rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    me.materials.append(material)
    o = bpy.data.objects.new(name, me)
    o.location = loc
    o.rotation_euler = rot
    collection.objects.link(o)
    return o


def box(name, size, loc, material, collection, rot=(0, 0, 0)):
    """Box with its base at loc (z = bottom)."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector((0, 0, size[2] / 2)), verts=bm.verts)
    return obj_from_bmesh(name, bm, material, collection, loc, rot)


def cyl(name, radius, depth, loc, material, collection, rot=(0, 0, 0), segments=16, radius2=None):
    """Cylinder (or cone, with radius2) with its base at loc."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius,
                          radius2=radius if radius2 is None else radius2, depth=depth)
    bmesh.ops.translate(bm, vec=Vector((0, 0, depth / 2)), verts=bm.verts)
    return obj_from_bmesh(name, bm, material, collection, loc, rot)


def sphere(name, radius, loc, material, collection, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=radius)
    bmesh.ops.scale(bm, vec=Vector(scale), verts=bm.verts)
    return obj_from_bmesh(name, bm, material, collection, loc)


def plane(name, w, h, loc, material, collection, rot=(math.pi / 2, 0, 0)):
    """Vertical plane w x h facing -Y by default (rot about X by 90 degrees), centred on loc."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    bmesh.ops.scale(bm, vec=Vector((w, h, 1)), verts=bm.verts)
    return obj_from_bmesh(name, bm, material, collection, loc, rot)


def text_surface(name, w, h, loc, rot, collection_parent=None, color=(0.92, 0.9, 0.85)):
    """A blank plane O will put text on. Its corners are exported per frame (render_shot.py)."""
    o = plane(f"txt_{name}", w, h, loc, mat(f"text_blank_{color}", color, 0.5), coll("TextSurfaces"), rot)
    o["text_surface"] = name
    return o


def parent_to(child, parent):
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


# ---------------------------------------------------------------- world, sun, render defaults

def world_and_render():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE"
    sc.render.fps = 24
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.eevee.taa_render_samples = 64
    sc.eevee.use_raytracing = True
    sc.eevee.use_shadows = True
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.film_transparent = False
    sc.render.motion_blur_shutter = 0.5  # 180 degrees (style spec)
    w = bpy.data.worlds.new("SkyWorld")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes.get("Background")
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(10)
    sky.sun_rotation = math.radians(100)  # azimuth, matches the sun lamp
    sky.sun_disc = True
    sky.altitude = 300
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.35
    w.mist_settings.start = 0.0
    w.mist_settings.depth = 300.0
    w.mist_settings.falloff = "LINEAR"
    sc.world = w
    vl = sc.view_layers[0]
    vl.use_pass_z = True
    vl.use_pass_mist = True
    vl.use_pass_normal = True
    aov = vl.aovs.add()
    aov.name = "building_mask"
    aov.type = "VALUE"

    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 4.0
    sun.use_temperature = True
    sun.temperature = 3400
    sun.angle = math.radians(1.0)
    so = bpy.data.objects.new("Sun", sun)
    # Sun 10 degrees up, from azimuth 100 (east, a little south): the light travels the other way.
    so.rotation_euler = sun_rotation(100, 10)
    coll("Lighting").objects.link(so)
    sky_fill = bpy.data.lights.new("SkyFill", "SUN")
    sky_fill.energy = 0.6
    sky_fill.color = (0.62, 0.74, 1.0)
    sky_fill.angle = math.radians(60)
    fo = bpy.data.objects.new("SkyFill", sky_fill)
    fo.rotation_euler = sun_rotation(280, 50)
    coll("Lighting").objects.link(fo)


def sun_rotation(azimuth_deg, elevation_deg):
    """Euler for a sun lamp shining from (azimuth, elevation): its -Z axis points away from the sun."""
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    to_sun = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    return (-to_sun).to_track_quat("-Z", "Y").to_euler()


# ---------------------------------------------------------------- terrain and fields

def ground():
    c = coll("Terrain")
    grass = mat("grass", (0.20, 0.30, 0.08), 0.9)
    dirt = mat("dirt", (0.32, 0.22, 0.13), 0.95)
    gravel = mat("gravel", (0.45, 0.42, 0.38), 0.9)
    asphalt = mat("asphalt", (0.06, 0.06, 0.06), 0.85)
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6000)
    obj_from_bmesh("ground", bm, grass, c, (0, 0, 0))
    # The yard's gravel drive, the farm road, and main street.
    box("drive", (4, 40, 0.02), (6, -24, 0), gravel, c)
    box("farm_road", (900, 7, 0.02), (0, -46, 0), asphalt, c)
    box("main_street", (12, 260, 0.02), (STREET_X, 380, 0), asphalt, c)
    # The cleared strip "where the cornfield used to stay", with the FUTURE SITE OF sign (S09).
    clear = ray(250, 0)
    box("cleared_plot", (90, 70, 0.03), (clear.x, clear.y, 0), dirt, c, (0, 0, ray_yaw()))


def corn_patch(name, origin, cols, rows, yaw=0.0):
    """A block of corn: one randomised row of stalks, arrayed into rows (rows 0.76 m apart)."""
    c = coll("Cornfield")
    stalk_mat = mat("corn", (0.35, 0.38, 0.10), 0.8)
    bm = bmesh.new()
    x = 0.0
    for i in range(cols):
        h = random.uniform(2.1, 2.7)
        lean = Vector((random.uniform(-0.06, 0.06), random.uniform(-0.06, 0.06), 1.0)).normalized()
        base = Vector((x + random.uniform(-0.08, 0.08), random.uniform(-0.1, 0.1), 0))
        geom = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=0.035, radius2=0.015, depth=h)
        rot = lean.to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation(base) @ rot @ Matrix.Translation((0, 0, h / 2)),
                            verts=geom["verts"])
        for k in range(5):  # leaves: drooping quads around the stalk
            ang = random.uniform(0, 2 * math.pi)
            z = h * (0.25 + 0.13 * k)
            d = Vector((math.cos(ang), math.sin(ang), 0))
            p0 = base + Vector((0, 0, z))
            p1 = p0 + d * 0.55 + Vector((0, 0, 0.15))
            p2 = p0 + d * 0.9 + Vector((0, 0, -0.15))
            side = d.cross(Vector((0, 0, 1))) * 0.05
            vs = [bm.verts.new(v) for v in (p0 - side, p0 + side, p1 + side, p2, p1 - side)]
            bm.faces.new(vs)
        x += 0.3
    o = obj_from_bmesh(name, bm, stalk_mat, c, origin, (0, 0, yaw))
    m = o.modifiers.new("rows", "ARRAY")
    m.use_relative_offset = False
    m.use_constant_offset = True
    m.constant_offset_displace = (0, 0.76, 0)
    m.count = rows
    return o


def fields():
    # East of the house the rows run along the campus ray, split by a farm track (side 14-20 m) that the singer
    # walks in S12, the halls ahead of him. The pasture (cows, kid) is the strip before d = 32 m. West of the
    # house, an axis-aligned field. Beyond, a corn-coloured ground plane carries the field to the horizon.
    yaw = ray_yaw()
    corn_patch("corn_east_a", ray(10, 2), 40, 120, yaw)
    corn_patch("corn_east_b", ray(32, 20), 230, 90, yaw)
    corn_patch("corn_east_c", ray(101, -50), 460, 200, yaw)
    track = ray(55, 17)
    box("farm_track", (6, 95, 0.03), (track.x, track.y, 0), mat("dirt", (0.32, 0.22, 0.13), 0.95), coll("Terrain"),
        (0, 0, yaw))
    corn_patch("corn_west", (-120, 20, 0), 300, 140)
    far = mat("corn_far", (0.33, 0.33, 0.10), 0.9)
    box("corn_far_e", (1600, 1400, 0.6), (900, 900, 0), far, coll("Cornfield"))
    box("corn_far_w", (1400, 1400, 0.6), (-900, 1100, 0), far, coll("Cornfield"))


def pasture_and_cows():
    c = coll("Animals")
    fence_m = mat("fence_wood", (0.45, 0.35, 0.25), 0.8)
    for i in range(24):  # pasture fence along the farm road
        box(f"pasture_post_{i}", (0.12, 0.12, 1.2), (40 + i * 4, -42, 0), fence_m, coll("Farm"))
    box("pasture_rail", (96, 0.06, 0.1), (86, -42, 1.0), fence_m, coll("Farm"))
    hide = mat("cow_hide", (0.85, 0.82, 0.78), 0.8)
    black = mat("cow_black", (0.05, 0.05, 0.05), 0.8)
    spots = [(60, -30), (68, -24), (75, -33), (83, -27), (92, -35), (99, -22), (106, -30), (70, -14)]
    for i, (x, y) in enumerate(spots):
        cow = bpy.data.objects.new(f"cow_{i}", None)
        cow.location = (x, y, 0)
        cow["faces"] = "building"  # render_shot.py turns every cow to face the nearest hall
        c.objects.link(cow)
        parts = [box(f"cow_{i}_body", (0.7, 1.9, 0.75), (0, 0, 0.75), hide if i % 2 else black, c),
                 box(f"cow_{i}_head", (0.35, 0.55, 0.4), (0, 1.15, 1.2), black if i % 2 else hide, c)]
        for lx, ly in ((-0.25, -0.75), (0.25, -0.75), (-0.25, 0.75), (0.25, 0.75)):
            parts.append(cyl(f"cow_{i}_leg", 0.07, 0.75, (lx, ly, 0), black, c))
        for p in parts:
            p.parent = cow


def water_tower():
    c = coll("Farm")
    steel = mat("tower_steel", (0.55, 0.57, 0.6), 0.5, 0.6)
    tank = mat("tower_tank", (0.82, 0.83, 0.85), 0.45, 0.3)
    base = Vector(WATER_TOWER)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        leg = cyl(f"tower_leg_{k}", 0.35, 31, base + Vector((math.cos(a) * 5, math.sin(a) * 5, 0)), steel, c)
    # A classic cylindrical tank under a conical roof (a sphere read as a ball in close-ups, S28b).
    cyl("tower_tank", 6.9, 10.0, base + Vector((0, 0, 31)), tank, c, segments=32)
    cyl("tower_cap", 7.1, 2.0, base + Vector((0, 0, 41)), tank, c, segments=32, radius2=1.0)
    # The gauge: a level board on the tank's south side, facing the farm. Its fill rises and falls with the
    # continuity table (render_shot.py scales gauge_fill); the board itself is a text surface for O.
    gauge_bg = plane("gauge_board", 2.0, 8.0, base + Vector((0, -7.0, 36)),
                     mat("gauge_board", (0.95, 0.95, 0.93), 0.5), c)
    fill = box("gauge_fill", (1.4, 0.05, 7.0), base + Vector((0, -7.06, 32.5)),
               mat("gauge_fill", (0.08, 0.30, 0.75), 0.4), c)
    fill["gauge"] = True
    text_surface("water_gauge", 2.0, 8.0, base + Vector((0, -7.1, 36)), (math.pi / 2, 0, 0))


def power_lines():
    """Poles every 60 m, 95 m east of the ray, from the farm road to the campus; three sagging wires."""
    c = coll("PowerLines")
    wood = mat("pole_wood", (0.28, 0.2, 0.13), 0.9)
    wire_m = mat("wire", (0.03, 0.03, 0.03), 0.5)
    poles = [ray(d, 95) for d in range(-60, 1500, 60)]
    for i, p in enumerate(poles):
        cyl(f"pole_{i}", 0.17, 12, p, wood, c, segments=8)
        box(f"pole_arm_{i}", (2.6, 0.12, 0.12), p + Vector((0, 0, 11.2)), wood, c, (0, 0, ray_yaw()))
    for k, off in enumerate((-1.1, 0.0, 1.1)):
        cu = bpy.data.curves.new(f"wire_{k}", "CURVE")
        cu.dimensions = "3D"
        cu.bevel_depth = 0.015
        sp = cu.splines.new("POLY")
        pts = []
        side = Vector((math.cos(math.radians(RAY_AZIMUTH)), -math.sin(math.radians(RAY_AZIMUTH)), 0)) * off
        for a, b in zip(poles, poles[1:]):
            for t in [i / 8 for i in range(8)]:
                p = a.lerp(b, t) + side
                p.z = 11.3 - 1.2 * 4 * t * (1 - t)  # sag
                pts.append(p)
        pts.append(poles[-1] + side + Vector((0, 0, 11.3)))
        sp.points.add(len(pts) - 1)
        for pt, p in zip(sp.points, pts):
            pt.co = (*p, 1)
        o = bpy.data.objects.new(f"wire_{k}", cu)
        o.data.materials.append(wire_m)
        c.objects.link(o)


# ---------------------------------------------------------------- the building

def campus():
    """Halls along the ray, each tagged with its distance d; floodlight masts; the fence; one LED."""
    root = coll("Building")
    concrete = mat("hall_concrete", (0.20, 0.205, 0.21), 0.7, mask=True)  # darker than the sky, so it reads
    roof_m = mat("hall_roof", (0.25, 0.26, 0.27), 0.6, mask=True)
    unit_m = mat("hall_units", (0.5, 0.52, 0.53), 0.5, 0.4, mask=True)
    lamp_m = mat("flood_lamp", (1, 1, 1), 0.3, emit=(0.85, 0.92, 1.0), emit_strength=0.0, mask=True)
    led_m = mat("hall_led", (0.1, 0.1, 0.1), 0.3, emit=(0.2, 0.5, 1.0), emit_strength=0.0, mask=True)
    fence_m = mat("campus_fence", (0.45, 0.47, 0.5), 0.5, 0.7, mask=True)
    L, W, H = HALL["length"], HALL["width"], HALL["height"]
    for i, d in enumerate(HALL_D):
        c = coll(f"Hall_{i:02d}", root)
        c["d"] = d
        centre = ray(d)
        yaw = ray_yaw()
        box(f"hall_{i:02d}", (W, L, H), centre, concrete, c, (0, 0, yaw))
        box(f"hall_{i:02d}_parapet", (W + 1, L + 1, 1.2), centre + Vector((0, 0, H)), roof_m, c, (0, 0, yaw))
        for k in range(6):  # rooftop chillers
            p = ray(d - L / 2 + 15 + k * 20, -30, H + 1.2)
            box(f"hall_{i:02d}_chiller_{k}", (14, 8, 4), p, unit_m, c, (0, 0, yaw))
            p = ray(d - L / 2 + 15 + k * 20, 30, H + 1.2)
            box(f"hall_{i:02d}_chillerb_{k}", (14, 8, 4), p, unit_m, c, (0, 0, yaw))
        for s in (-1, 1):  # floodlight masts at the hall's near corners
            mp = ray(d - L / 2 - 6, s * (W / 2 + 6))
            cyl(f"hall_{i:02d}_mast_{s}", 0.5, 60, mp, unit_m, c, segments=8)
            box(f"hall_{i:02d}_lamps_{s}", (5, 1.2, 3), mp + Vector((0, 0, 58)), lamp_m, c, (0, 0, yaw))
            spot = bpy.data.lights.new(f"hall_{i:02d}_flood_{s}", "SPOT")
            spot.energy = 0.0
            spot.spot_size = math.radians(70)
            spot.use_temperature = True
            spot.temperature = 5600
            so = bpy.data.objects.new(f"hall_{i:02d}_flood_{s}", spot)
            so.location = mp + Vector((0, 0, 57))
            so.rotation_euler = (Vector((0, 0, -1)) + (ray(0) - ray(1)) * 0.9).to_track_quat("-Z", "Y").to_euler()
            so["flood"] = True
            c.objects.link(so)
        # Fence along the hall's near end (the dog's leash ends up tied to it, S27).
        fp = ray(d - L / 2 - 20)
        box(f"hall_{i:02d}_fence", (W + 40, 0.05, 2.4), fp, fence_m, c, (0, 0, yaw))
        for k in range(17):
            box(f"hall_{i:02d}_fpost_{k}", (0.1, 0.1, 2.6), ray(d - L / 2 - 20, -80 + k * 10), fence_m, c)
        # One status LED on the near facade, at door height: "The building's LED blinks" (S30).
        box(f"hall_{i:02d}_led", (1.2, 0.3, 0.5), ray(d - L / 2 - 0.2, 0, 6), led_m, c, (0, 0, yaw))
    # The building's light on the farm in the final chorus: a broad, cool area light from the nearest halls.
    bl = bpy.data.lights.new("building_wash", "AREA")
    bl.shape = "RECTANGLE"
    bl.size, bl.size_y = 120, 40
    bl.energy = 0.0
    bl.use_temperature = True
    bl.temperature = 5800
    bo = bpy.data.objects.new("building_wash", bl)
    bo.location = ray(60, 0, 30)
    bo.rotation_euler = (ray(-1) - ray(0) + Vector((0, 0, -0.35))).to_track_quat("-Z", "Y").to_euler()
    coll("Lighting").objects.link(bo)
    # B1's construction site: tower cranes where B2 will build.
    crane_m = mat("crane_yellow", (0.85, 0.6, 0.05), 0.5, 0.3)
    cc = coll("Cranes")
    for k, d in enumerate(CRANE_D):
        p = ray(d, -40 + 40 * k)
        box(f"crane_{k}_mast", (2.5, 2.5, 70), p, crane_m, cc)
        jib = box(f"crane_{k}_jib", (60, 1.8, 1.8), p + Vector((15, 0, 70)), crane_m, cc,
                  (0, 0, random.uniform(0, math.pi)))
        box(f"crane_{k}_counter", (4, 3, 3), p + Vector((-12, 0, 68)), crane_m, cc)


# ---------------------------------------------------------------- farmhouse, porch, kitchen, yard

def mannequin(name, height, loc, yaw, colors, pose="stand", collection=None):
    """A stand-in figure: legs, torso, arms, head. pose: stand | point | hold_mug | two_fingers | walk | turned."""
    c = collection or coll("Characters")
    root = bpy.data.objects.new(name, None)
    root.location = loc
    root.rotation_euler = (0, 0, yaw)
    root["pose"] = pose
    c.objects.link(root)
    s = height / 1.8
    shirt, pants, skin = (mat(f"{name}_shirt", colors[0], 0.8), mat(f"{name}_pants", colors[1], 0.8),
                          mat("skin", (0.80, 0.58, 0.45), 0.6))
    parts = []
    stride = 0.18 * s if pose == "walk" else 0.0
    for lx, fwd in ((-0.11, stride), (0.11, -stride)):
        parts.append(cyl(f"{name}_leg", 0.075 * s, 0.85 * s, (lx * s, fwd, 0), pants, c))
    parts.append(cyl(f"{name}_torso", 0.19 * s, 0.62 * s, (0, 0, 0.85 * s), shirt, c, radius2=0.21 * s))
    parts.append(sphere(f"{name}_head", 0.115 * s, (0, 0, 1.6 * s), skin, c, (0.9, 1.0, 1.1)))
    sh = 1.42 * s
    arm = 0.62 * s

    def limb(side, direction):
        d = Vector(direction).normalized()
        o = cyl(f"{name}_arm", 0.055 * s, arm, (side * 0.25 * s, 0, sh), shirt, c)
        o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        return o

    # Arms point along direction vectors (in the figure's space: +Y is where it faces).
    arms = {"stand": ((-1, (-0.1, 0, -1)), (1, (0.1, 0, -1))),
            "walk": ((-1, (-0.1, -0.3, -1)), (1, (0.1, 0.3, -1))),
            "point": ((-1, (-0.1, 0, -1)), (1, (0.15, 1, 0.1))),
            "hold_mug": ((-1, (-0.1, 0, -1)), (1, (-0.2, 0.7, 0.2))),
            "two_fingers": ((-1, (-0.1, 0, -1)), (1, (0.2, 0.3, 1))),
            "turned": ((-1, (-0.1, 0, -1)), (1, (0.1, 0, -1)))}[pose]
    for side, direction in arms:
        parts.append(limb(side, direction))
    for p in parts:
        p.parent = root
    return root


def farmhouse():
    c = coll("Farm")
    siding = mat("siding_white", (0.86, 0.85, 0.80), 0.7)
    trim = mat("trim", (0.95, 0.95, 0.93), 0.6)
    roof_m = mat("roof_shingle", (0.18, 0.16, 0.15), 0.85)
    deck = mat("porch_deck", (0.55, 0.42, 0.30), 0.7)
    glass = mat("window_glass", (0.08, 0.1, 0.12), 0.1, 0.0)
    door_m = mat("door_red", (0.45, 0.08, 0.06), 0.5)
    hx0, hx1, hy0, hy1 = HOUSE
    w, d = hx1 - hx0, hy1 - hy0
    # Walls as four slabs so the kitchen inside is real; a window hole is left in the north wall.
    t = 0.25
    box("house_wall_s", (w, t, 3.2), ((hx0 + hx1) / 2, hy0, 0), siding, c)
    box("house_wall_w", (t, d, 3.2), (hx0, (hy0 + hy1) / 2, 0), siding, c)
    box("house_wall_e", (t, d, 3.2), (hx1, (hy0 + hy1) / 2, 0), siding, c)
    kx0 = KITCHEN[0]
    box("house_wall_n_a", (kx0 - hx0 + 1.5, t, 3.2), ((hx0 + kx0 + 1.5) / 2, hy1, 0), siding, c)
    box("house_wall_n_below", (2.0, t, 1.5), (kx0 + 2.5, hy1, 0), siding, c)          # under the window
    box("house_wall_n_above", (2.0, t, 0.6), (kx0 + 2.5, hy1, 2.6), siding, c)        # over the window
    box("house_wall_n_b", (hx1 - kx0 - 3.5, t, 3.2), ((kx0 + 3.5 + hx1) / 2, hy1, 0), siding, c)
    box("house_floor", (w, d, 0.6), ((hx0 + hx1) / 2, (hy0 + hy1) / 2, 0), deck, c)
    # Gable roof along X.
    bm = bmesh.new()
    r = [bm.verts.new(v) for v in ((hx0 - 0.6, hy0 - 0.6, 3.2), (hx1 + 0.6, hy0 - 0.6, 3.2),
                                   (hx1 + 0.6, hy1 + 0.6, 3.2), (hx0 - 0.6, hy1 + 0.6, 3.2),
                                   (hx0 - 0.6, (hy0 + hy1) / 2, 5.6), (hx1 + 0.6, (hy0 + hy1) / 2, 5.6))]
    bm.faces.new((r[0], r[1], r[5], r[4]))
    bm.faces.new((r[3], r[4], r[5], r[2]))
    bm.faces.new((r[0], r[4], r[3]))
    bm.faces.new((r[1], r[2], r[5]))
    obj_from_bmesh("house_roof", bm, roof_m, c)
    # Front windows and door on the porch wall.
    for x in (hx0 + 2.0, hx0 + 4.2, hx1 - 3.0):
        plane(f"house_window_{x:.0f}", 1.1, 1.4, (x, hy0 - 0.13, 1.9), glass, c)
        box(f"house_shutter_{x:.0f}", (1.3, 0.05, 1.6), (x, hy0 - 0.12, 1.2), trim, c)
    plane("house_door", 1.0, 2.1, (hx0 + 6.6, hy0 - 0.14, 1.65), door_m, c)

    # The porch: deck, posts, roof, rail, steps, rocking chair, flag.
    py0 = hy0 - 2.6
    box("porch_deck", (w, 2.6, 0.6), ((hx0 + hx1) / 2, hy0 - 1.3, 0), deck, c)
    for k in range(5):
        box(f"porch_post_{k}", (0.15, 0.15, 2.5), (hx0 + 0.2 + k * (w - 0.4) / 4, py0 + 0.15, 0.6), trim, c)
    box("porch_roof", (w + 0.4, 2.9, 0.15), ((hx0 + hx1) / 2, hy0 - 1.35, 3.1), roof_m, c)
    # Rails with a wide flat cap (top at RAIL_TOP), wide enough to cool a pie on (S31).
    box("porch_rail_w", ((w - 1.6) / 2 - 0.3, 0.3, 0.06), (hx0 + (w - 1.6) / 4, py0 + 0.15, RAIL_TOP - 0.06), trim, c)
    box("porch_rail_e", ((w - 1.6) / 2 - 0.3, 0.3, 0.06), (hx1 - (w - 1.6) / 4, py0 + 0.15, RAIL_TOP - 0.06), trim, c)
    for k in range(3):
        box(f"porch_step_{k}", (1.6, 0.35, 0.2 * (3 - k)), ((hx0 + hx1) / 2, py0 - 0.35 * (k + 0.5), 0), deck, c)
    chair = mat("chair_wood", (0.4, 0.28, 0.18), 0.7)
    box("rocker_seat", (0.6, 0.6, 0.08), (hx0 + 1.5, hy0 - 1.0, 1.05), chair, c)
    box("rocker_back", (0.6, 0.08, 0.9), (hx0 + 1.5, hy0 - 0.7, 1.1), chair, c)
    # Flag on an angled pole from the east-most post.
    # The pole leans 35 degrees out from the post, away from the house (-Y), under the roof edge; the flag
    # hangs from it, hoist along the pole's upper 0.95 m, fly hanging out and down, in the pole's plane.
    lean = math.radians(35)
    pole_base = Vector((hx1 - 0.2, py0 + 0.08, 2.4))
    cyl("flag_pole", 0.025, 2.2, pole_base, trim, c, (lean, 0, 0))
    along = Vector((0, -math.sin(lean), math.cos(lean)))
    across = Vector((0, -math.cos(lean), -math.sin(lean)))
    bm = bmesh.new()
    corners = [along * 1.2, along * 2.15, along * 2.15 + across * 1.5, along * 1.2 + across * 1.5]
    bm.faces.new([bm.verts.new(v + Vector((0.03, 0, 0))) for v in corners])
    flag = obj_from_bmesh("flag", bm, mat("flag", (0.55, 0.08, 0.1), 0.8), c, pole_base)
    flag["flag"] = True
    # The pie on the rail (S31) and its tin; the mug lives with the singer.
    tin = mat("pie_tin", (0.8, 0.8, 0.82), 0.25, 1.0)
    crust = mat("pie_crust", (0.75, 0.5, 0.25), 0.7)
    # A 9-inch tin flares out: 19 cm base, 23 cm rim, 3 cm deep, with a flat lip; the pie domes just above the rim.
    pie_at = Vector((hx1 - 1.2, py0 + 0.15, RAIL_TOP))
    pie_tin = cyl("pie_tin", 0.095, 0.03, pie_at, tin, coll("Props"), segments=32, radius2=0.115)
    cyl("pie_tin_lip", 0.125, 0.003, (0, 0, 0.028), tin, coll("Props"), segments=32).parent = pie_tin
    pie = cyl("pie", 0.112, 0.012, pie_at + Vector((0, 0, 0.03)), crust, coll("Props"), segments=32, radius2=0.1)
    cyl("pie_dome", 0.1, 0.008, (0, 0, 0.012), crust, coll("Props"), segments=32, radius2=0.07).parent = pie

    # Kitchen (inside the north-east corner): table, empty chair with a name tag, oven, sink under the window,
    # overhead bulb.
    k = coll("Kitchen")
    kx0, ky0, kx1, ky1 = KITCHEN
    floor = mat("kitchen_floor", (0.6, 0.55, 0.45), 0.6)
    cab = mat("cabinet", (0.75, 0.78, 0.72), 0.5)
    box("kitchen_floor", (kx1 - kx0, ky1 - ky0, 0.02), ((kx0 + kx1) / 2, (ky0 + ky1) / 2, 0.6), floor, k)
    box("kitchen_partition", (0.15, ky1 - ky0, 2.6), (kx0, (ky0 + ky1) / 2, 0.6), siding, k)
    box("kitchen_ceiling", (kx1 - kx0, ky1 - ky0, 0.1), ((kx0 + kx1) / 2, (ky0 + ky1) / 2, 3.2), trim, k)
    box("kitchen_counter", (3.0, 0.6, 0.9), (kx0 + 2.5, ky1 - 0.45, 0.6), cab, k)
    box("oven", (0.75, 0.65, 0.9), (kx1 - 0.5, ky0 + 1.6, 0.6), mat("oven", (0.85, 0.85, 0.82), 0.3, 0.2), k,
        (0, 0, math.pi / 2))
    table_m = mat("kitchen_table", (0.5, 0.36, 0.22), 0.6)
    tx, ty = (kx0 + kx1) / 2 - 0.3, (ky0 + ky1) / 2 - 0.4
    box("kitchen_table", (1.4, 0.9, 0.05), (tx, ty, 1.35), table_m, k)
    for lx in (-0.6, 0.6):
        for ly in (-0.35, 0.35):
            box("kitchen_table_leg", (0.06, 0.06, 0.75), (tx + lx, ty + ly, 0.6), table_m, k)
    for side, name in ((-1, "kitchen_chair_grandma"), (1, "kitchen_chair_empty")):
        cx = tx + side * 1.0
        box(f"{name}_seat", (0.45, 0.45, 0.05), (cx, ty, 1.05), table_m, k)
        box(f"{name}_back", (0.05, 0.45, 0.6), (cx + side * 0.22, ty, 1.1), table_m, k)
    text_surface("chair_tag", 0.22, 0.1, (tx + 1.2, ty - 0.24, 1.45), (math.pi / 2, 0, 0))
    text_surface("power_bill", 0.216, 0.279, (tx - 0.15, ty, 1.405), (0, 0, 0.2))
    bulb = bpy.data.lights.new("kitchen_bulb", "POINT")
    bulb.energy = 60.0
    bulb.use_temperature = True
    bulb.temperature = 2700
    bulb.shadow_soft_size = 0.05
    bo = bpy.data.objects.new("kitchen_bulb", bulb)
    bo.location = (tx, ty, 2.9)
    bo["practical"] = "kitchen"
    k.objects.link(bo)
    sphere("kitchen_bulb_glass", 0.06, (tx, ty, 2.95), mat("bulb_glass", (1, 0.9, 0.7), 0.2,
                                                          emit=(1, 0.85, 0.6), emit_strength=8), k)
    # Porch light by the door.
    pl = bpy.data.lights.new("porch_light", "POINT")
    pl.energy = 25.0
    pl.use_temperature = True
    pl.temperature = 2800
    plo = bpy.data.objects.new("porch_light", pl)
    plo.location = (hx0 + 7.4, hy0 - 0.4, 2.6)
    plo["practical"] = "porch"
    c.objects.link(plo)


def yard_and_people():
    hx0, hx1, hy0, hy1 = HOUSE
    py0 = hy0 - 2.6
    flannel, jeans = (0.55, 0.12, 0.10), (0.15, 0.2, 0.32)
    # One stand-in per pose; render_shot.py shows the one a shot casts and places it.
    for pose in ("hold_mug", "point", "walk", "two_fingers", "stand"):
        s = mannequin(f"singer_{pose}", 1.82, (hx1 - 1.65, py0 + 1.1, 0.6), math.pi, (flannel, jeans), pose)
        s["role"] = "singer"
    mug_white = mat("mug_white", (0.93, 0.93, 0.9), 0.3)
    mug = cyl("mug_hand", 0.045, 0.1, (0.18, 0.42, 1.36), mug_white, coll("Props"))
    mug.parent = bpy.data.objects["singer_hold_mug"]
    text_surface("mug_hand", 0.08, 0.07, (0.18, 0.375, 1.41), (math.pi / 2, 0, 0)).parent = mug.parent
    kx0, ky0, kx1, ky1 = KITCHEN
    tx, ty = (kx0 + kx1) / 2 - 0.3, (ky0 + ky1) / 2 - 0.4
    cyl("mug_table", 0.045, 0.1, (tx + 0.3, ty + 0.1, 1.4), mug_white, coll("Props"))
    text_surface("mug_table", 0.08, 0.07, (tx + 0.3, ty + 0.055, 1.45), (math.pi / 2, 0, 0))
    cyl("mug_rail", 0.045, 0.1, (hx1 - 1.5, py0 + 0.15, RAIL_TOP), mug_white, coll("Props"))
    text_surface("mug_rail", 0.08, 0.07, (hx1 - 1.5, py0 + 0.195, RAIL_TOP + 0.05), (math.pi / 2, 0, math.pi))  # faces the porch (S31)
    dog_m = mat("dog_golden", (0.75, 0.52, 0.22), 0.8)
    dog = bpy.data.objects.new("dog", None)
    dog.location = (hx1 - 2.4, py0 + 0.7, 0.6)
    dog.rotation_euler = (0, 0, math.radians(150))
    dog["role"] = "dog"
    coll("Animals").objects.link(dog)
    for p in (box("dog_body", (0.3, 0.75, 0.32), (0, 0, 0.35), dog_m, coll("Animals")),
              box("dog_head", (0.22, 0.28, 0.24), (0, 0.45, 0.6), dog_m, coll("Animals")),
              cyl("dog_tail", 0.03, 0.35, (0, -0.4, 0.55), dog_m, coll("Animals"), (math.radians(-120), 0, 0))):
        p.parent = dog
    for lx, ly in ((-0.1, -0.28), (0.1, -0.28), (-0.1, 0.28), (0.1, 0.28)):
        cyl("dog_leg", 0.04, 0.35, (lx, ly, 0), dog_m, coll("Animals")).parent = dog
    # The leash, tied to the nearest hall's fence (shown only when the dog is gone, S27).
    # It hangs straight down from where it is tied at 0.9 m, the empty collar at its end just above the grass.
    leash_m = mat("leash_red", (0.6, 0.05, 0.05), 0.6)
    tie = ray(HALL_D[0] - HALL["length"] / 2 - 20.2, -6, 0.9)
    leash = cyl("leash", 0.012, 0.7, tie - Vector((0, 0, 0.7)), leash_m, coll("Props"))
    leash["leash"] = True
    collar = cyl("leash_collar", 0.07, 0.025, (0, 0, -0.07), leash_m, coll("Props"), (math.pi / 2, 0, 0), segments=20)
    collar.parent = leash
    # Grandma at the kitchen (oven / window), the kid in the pasture with the kite.
    g = mannequin("grandma", 1.6, (kx1 - 1.3, ky0 + 1.6, 0.6), -math.pi / 2,
                  ((0.45, 0.55, 0.7), (0.35, 0.3, 0.35)), "stand")
    g["role"] = "grandma"
    for pose in ("two_fingers", "stand"):
        kid = mannequin(f"kid_{pose}", 1.25, (64, -12, 0), math.radians(20),
                        ((0.9, 0.75, 0.1), (0.2, 0.25, 0.45)), pose)
        kid["role"] = "kid"
    tangled = plane("kite_tangled", 0.6, 0.5, (0.1, 0.35, 0.85), mat("kite", (0.85, 0.15, 0.12), 0.6), coll("Props"),
                    (math.radians(60), 0.4, 0.2))
    tangled.parent = bpy.data.objects["kid_stand"]
    kite_m = mat("kite", (0.85, 0.15, 0.12), 0.6)
    kite = plane("kite", 0.9, 1.1, (80.0, -4.0, 18.0), kite_m, coll("Props"), (math.radians(70), 0, 0.3))
    kite["kite"] = True
    cu = bpy.data.curves.new("kite_string", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.004
    sp = cu.splines.new("POLY")
    a, b = Vector((64.2, -11.6, 1.55)), kite.location
    pts = [a.lerp(b, t) + Vector((0, 0, -2.5 * 4 * t * (1 - t))) for t in [i / 12 for i in range(13)]]
    sp.points.add(len(pts) - 1)
    for pt, p in zip(sp.points, pts):
        pt.co = (*p, 1)
    so = bpy.data.objects.new("kite_string", cu)
    so.data.materials.append(mat("string", (0.9, 0.9, 0.85), 0.6))
    coll("Props").objects.link(so)


# ---------------------------------------------------------------- main street: diner, church, signs

def main_street():
    c = coll("MainStreet")
    sx = STREET_X
    brick = mat("brick", (0.45, 0.2, 0.14), 0.85)
    clap = mat("clapboard_blue", (0.55, 0.65, 0.72), 0.7)
    clap2 = mat("clapboard_yellow", (0.85, 0.75, 0.45), 0.7)
    glass = mat("storefront_glass", (0.07, 0.09, 0.1), 0.1)
    walk = mat("sidewalk", (0.62, 0.6, 0.56), 0.8)
    for side in (-1, 1):
        box(f"sidewalk_{side}", (3, 260, 0.15), (sx + side * 7.5, 380, 0), walk, c)
    # Storefronts on both sides; low (one storey) on the east so the campus shows over them.
    for k, y in enumerate(range(300, 456, 14)):  # stops short of the church lot (marquee)
        if abs(y - DINER[1]) >= 14:  # stores are 12 m deep, the diner 16 m: keep them clear of each other
            box(f"store_w_{k}", (10, 12, 6 + (k % 3)), (sx - 14, y, 0), [brick, clap, clap2][k % 3], c)
            plane(f"store_w_glass_{k}", 7, 2.4, (sx - 8.95, y, 1.8), glass, c, (math.pi / 2, 0, math.pi / 2))
        if abs(y - DINER[1]) < 26:
            continue  # a parking lot across from the diner: its window looks over it to the campus (S20)
        box(f"store_e_{k}", (10, 12, 4.5), (sx + 14, y, 0), [clap2, brick, clap][k % 3], c)
        plane(f"store_e_glass_{k}", 7, 2.4, (sx + 8.95, y, 1.8), glass, c, (math.pi / 2, 0, -math.pi / 2))
    # Yard signs: south end of the street, in the lawns of the first houses (FOLKS LIKE US / ... TOO, via O).
    stake = mat("sign_stake", (0.5, 0.5, 0.5), 0.5, 0.8)
    for k, y in enumerate(range(262, 296, 4)):
        for side in (-1, 1):
            x = sx + side * 11
            cyl(f"sign_stake_{side}_{k}", 0.01, 0.6, (x, y, 0), stake, c, segments=6)
            text_surface(f"yard_sign_{'w' if side < 0 else 'e'}{k}", 0.6, 0.45, (x, y, 0.75),
                         (math.pi / 2, 0, -side * math.pi / 2))
    # The church at the north end, its marquee by the street.
    ch = coll("Church", c)
    box("church_nave", (14, 24, 9), (sx - 22, 490, 0), mat("church_white", (0.92, 0.92, 0.9), 0.7), ch)
    box("church_tower", (5, 5, 20), (sx - 13, 480, 0), mat("church_white", (0.92, 0.92, 0.9), 0.7), ch)
    cyl("church_spire", 3.2, 8, (sx - 13, 480, 20), mat("roof_shingle", (0.18, 0.16, 0.15), 0.85), ch,
        segments=4, radius2=0.01)
    box("marquee_frame", (3.4, 0.4, 1.9), (sx - 9.5, 470, 0.9), mat("marquee_frame", (0.2, 0.22, 0.3), 0.5), ch,
        (0, 0, math.pi / 2))
    for side in (-1, 1):
        box(f"marquee_leg_{side}", (0.15, 0.15, 0.9), (sx - 9.5, 470 + side * 1.4, 0), stake, ch)
    text_surface("marquee", 3.0, 1.5, (sx - 9.28, 470, 1.85), (math.pi / 2, 0, math.pi / 2),
                 color=(0.95, 0.95, 0.92))

    # The diner: west side of the street, its big window facing east across the street to the campus.
    d = coll("Diner")
    dx, dy = DINER
    wall = mat("diner_wall", (0.85, 0.78, 0.65), 0.7)
    chrome = mat("chrome", (0.8, 0.8, 0.82), 0.2, 1.0)
    vinyl = mat("vinyl_red", (0.6, 0.06, 0.06), 0.5)
    floor = mat("checker", (0.7, 0.7, 0.7), 0.4)
    box("diner_floor", (12, 16, 0.1), (dx, dy, 0), floor, d)
    box("diner_wall_w", (0.3, 16, 4), (dx - 6, dy, 0), wall, d)
    box("diner_wall_s", (12, 0.3, 4), (dx, dy - 8, 0), wall, d)
    box("diner_wall_n", (12, 0.3, 4), (dx, dy + 8, 0), wall, d)
    box("diner_roof", (12.6, 16.6, 0.3), (dx, dy, 4), wall, d)
    # East (street) wall: a long window from 1.0 m to 3.0 m.
    box("diner_wall_e_low", (0.3, 16, 1.0), (dx + 6, dy, 0), chrome, d)
    box("diner_wall_e_high", (0.3, 16, 1.0), (dx + 6, dy, 3.0), wall, d)
    for k in range(5):
        box(f"diner_mullion_{k}", (0.3, 0.12, 2.0), (dx + 6, dy - 8 + k * 4, 1.0), chrome, d)
    for k in range(4):  # booths along the window
        y = dy - 6 + k * 3.8
        box(f"booth_table_{k}", (1.0, 1.4, 0.05), (dx + 4.9, y, 0.75), chrome, d)
        box(f"booth_a_{k}", (0.6, 1.4, 0.45), (dx + 4.9, y - 1.1, 0), vinyl, d)
        box(f"booth_b_{k}", (0.6, 1.4, 0.45), (dx + 4.9, y + 1.1, 0), vinyl, d)
    box("counter", (1.0, 10, 1.1), (dx - 2.5, dy, 0), mat("counter", (0.85, 0.3, 0.25), 0.4), d)
    for k in range(8):
        cyl(f"stool_{k}", 0.2, 0.75, (dx - 1.6, dy - 4.2 + k * 1.2, 0), vinyl, d, segments=12)
    # TV wall on the south wall: 4 x 3 screens, each a text surface (O fills them with the dozen ads, S20).
    tvm = mat("tv_frame", (0.04, 0.04, 0.04), 0.4)
    for r in range(3):
        for col in range(4):
            x, z = dx - 4.2 + col * 2.8, 1.3 + r * 0.95
            box(f"tv_{r}{col}", (1.5, 0.12, 0.88), (x, dy - 7.8, z - 0.44), tvm, d)
            text_surface(f"tv_{r}{col}", 1.4, 0.79, (x, dy - 7.73, z), (math.pi / 2, 0, 0), color=(0.2, 0.25, 0.3))
    # Patrons: at the counter and in booths, all facing in, none looking out of the window (brief).
    shirts = [(0.3, 0.45, 0.3), (0.6, 0.55, 0.4), (0.25, 0.3, 0.5), (0.7, 0.3, 0.2), (0.4, 0.4, 0.45),
              (0.55, 0.15, 0.2)]
    for k, (x, y, yaw) in enumerate([(dx - 1.6, dy - 3.0, math.pi / 2), (dx - 1.6, dy - 0.6, math.pi / 2),
                                     (dx - 1.6, dy + 1.8, math.pi / 2), (dx + 4.7, dy - 7.1, 0),
                                     (dx + 4.7, dy - 1.0, math.pi), (dx + 4.7, dy + 2.8, 0)]):
        p = mannequin(f"patron_{k}", 1.75, (x, y, 0.15), yaw, (shirts[k], (0.2, 0.2, 0.25)), "stand", d)
        p["role"] = "patron"
    lamp = bpy.data.lights.new("diner_lights", "AREA")
    lamp.size, lamp.size_y = 10, 14
    lamp.shape = "RECTANGLE"
    lamp.energy = 900
    lamp.use_temperature = True
    lamp.temperature = 3200
    lo = bpy.data.objects.new("diner_lights", lamp)
    lo.location = (dx, dy, 3.85)
    lo["practical"] = "diner"
    d.objects.link(lo)


def future_site_sign():
    """S09: FUTURE SITE OF, the rest hidden under bunting, at the cleared plot's edge."""
    c = coll("Props")
    p = Vector(FUTURE_SIGN)
    wood = mat("sign_post", (0.4, 0.3, 0.2), 0.8)
    for s in (-1.4, 1.4):
        box("fs_post", (0.15, 0.15, 3.2), p + Vector((s, 0, 0)), wood, c)
    text_surface("future_site", 3.2, 1.8, p + Vector((0, -0.1, 2.2)), (math.pi / 2, 0, 0))
    bunting = mat("bunting", (0.8, 0.1, 0.12), 0.7)
    for k in range(8):  # pennants hanging over the lower part of the board
        bm = bmesh.new()
        x = -1.5 + k * 0.42
        v = [bm.verts.new(q) for q in ((x, 0, 0.3), (x + 0.4, 0, 0.3), (x + 0.2, 0, -0.35))]
        bm.faces.new(v)
        obj_from_bmesh(f"bunting_{k}", bm, [bunting, mat("bunting_w", (0.9, 0.9, 0.88), 0.7),
                                            mat("bunting_b", (0.1, 0.15, 0.45), 0.7)][k % 3],
                       c, p + Vector((0, -0.25, 1.9)))
    for side in (-1, 1):
        for k in range(10):  # surveyor stakes with flagging tape
            box("stake", (0.04, 0.04, 0.8), p + Vector((side * (4 + k * 2.5), 8 + k * 1.5, 0)), wood, c)


# ---------------------------------------------------------------- layout constants (used above)

HOUSE = (-14.0, -2.0, -4.0, 4.0)      # x0, x1, y0, y1 of the farmhouse walls (porch south of y0)
KITCHEN = (-7.0, 0.2, -2.0, 3.8)      # x0, y0, x1, y1 inside the house's north-east corner
STREET_X = -40.0                      # main street runs north-south at this x, y 250..510
DINER = (-55.0, 400.0)                # diner centre, west of the street; window faces east
WATER_TOWER = (150.0, 20.0, 0.0)
RAIL_TOP = 1.58
FUTURE_SIGN = (52.0, -4.0, 0.0)          # S09 foreground, at the corn's south edge


def main():
    reset()
    world_and_render()
    ground()
    fields()
    pasture_and_cows()
    water_tower()
    power_lines()
    campus()
    farmhouse()
    yard_and_people()
    main_street()
    future_site_sign()
    sc = bpy.context.scene
    sc["ray_azimuth"] = RAY_AZIMUTH
    sc["stage_min_d"] = STAGE_MIN_D
    sc["hall_d"] = HALL_D
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
    n = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
    print(f"saved {OUT}: {len(bpy.data.objects)} objects, {n} base faces")


if __name__ == "__main__":
    main()
