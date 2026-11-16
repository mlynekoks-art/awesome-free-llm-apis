"""Render setups: neutral studio still with a 1.8 m reference figure, and an overcast
Nordic-sky line-up.  Cycles CPU, modest samples, OpenImageDenoise."""
import math
import bpy
import numpy as np
from mathutils import Vector

from . import mats


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    return sc


def cycles(sc, samples=96, res=(1280, 720)):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.02
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 2
    sc.cycles.transparent_max_bounces = 48
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.threads_mode = "AUTO"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Base Contrast" if "AgX - Base Contrast" in [
        i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items] else "None"


# ----------------------------------------------------------------------------- figure
def human(loc=(0, 0, 0), height=1.8, name="Human_1.8m"):
    """Simple neutral mannequin, exactly `height` tall (feet at loc z)."""
    s = height / 1.8
    parts = []

    def cyl(a, b, r):
        a, b = Vector(a) * s, Vector(b) * s
        d = b - a
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r * s, depth=d.length, location=(a + b) / 2)
        o = bpy.context.active_object
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
        parts.append(o)

    def sph(c, r, sz=(1, 1, 1)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=r * s, location=Vector(c) * s)
        o = bpy.context.active_object
        o.scale = sz
        parts.append(o)

    for x in (-0.1, 0.1):
        cyl((x, 0, 0.04), (x * 0.95, 0, 0.5), 0.06)       # lower leg
        cyl((x * 0.95, 0, 0.5), (x * 0.9, 0, 0.92), 0.075)  # thigh
        sph((x, 0.04, 0.035), 0.06, (0.9, 1.9, 0.6))       # foot
        sph((x * 0.95, 0, 0.5), 0.065)
    sph((0, 0, 0.98), 0.17, (1.0, 0.65, 0.55))            # pelvis
    cyl((0, 0, 0.98), (0, 0, 1.45), 0.15)                 # torso
    sph((0, 0, 1.43), 0.2, (1.0, 0.6, 0.45))               # shoulders
    cyl((0, 0, 1.48), (0, 0, 1.57), 0.05)                  # neck
    sph((0, 0, 1.685), 0.115, (0.85, 0.95, 1.0))           # head -> top at 1.80
    for x in (-1, 1):
        cyl((x * 0.2, 0, 1.43), (x * 0.24, 0, 1.12), 0.045)
        cyl((x * 0.24, 0, 1.12), (x * 0.26, 0.02, 0.84), 0.038)
        sph((x * 0.26, 0.02, 0.8), 0.045)
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    zmin = min((ob.matrix_world @ v.co).z for v in ob.data.vertices)
    zmax = max((ob.matrix_world @ v.co).z for v in ob.data.vertices)
    sc = height / (zmax - zmin)
    ob.scale = (sc, sc, sc)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    zmin = min(v.co.z for v in ob.data.vertices)
    ob.location = Vector(loc) - Vector((0, 0, zmin))
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mats.flat("Mannequin", (0.32, 0.30, 0.28), 0.55))
    return ob


# ----------------------------------------------------------------------------- framing
def camera_fit(sc, bmin, bmax, azimuth_deg=-28.0, elevation_deg=6.0, lens=50.0, margin=1.12,
               target_z_frac=0.5, ortho=False):
    bmin, bmax = np.array(bmin), np.array(bmax)
    centre = (bmin + bmax) / 2
    centre[2] = bmin[2] + (bmax[2] - bmin[2]) * target_z_frac
    size = bmax - bmin
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = lens
    cam_data.sensor_width = 36
    cam_data.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new("Cam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    az, el = math.radians(azimuth_deg), math.radians(elevation_deg)
    view = np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
    aspect = sc.render.resolution_x / sc.render.resolution_y
    hfov = 2 * math.atan(18 / lens)
    vfov = 2 * math.atan(math.tan(hfov / 2) / aspect)
    # project the box extent onto camera axes
    right = np.cross(-view, [0, 0, 1])
    right /= np.linalg.norm(right)
    upv = np.cross(right, -view)
    corners = np.array([[x, y, z] for x in (bmin[0], bmax[0]) for y in (bmin[1], bmax[1]) for z in (bmin[2], bmax[2])])
    rel = corners - centre
    half_w = np.abs(rel @ right).max() * margin
    half_h = np.abs(rel @ upv).max() * margin
    depth = np.abs(rel @ view).max()
    if ortho:
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = max(2 * half_w, 2 * half_h * aspect)
        dist = depth + 50
    else:
        dist = max(half_w / math.tan(hfov / 2), half_h / math.tan(vfov / 2)) + depth
    cam.location = Vector(centre + view * dist)
    cam.rotation_mode = "QUATERNION"
    cam.rotation_quaternion = Vector(-view).to_track_quat("-Z", "Y")
    cam_data.clip_end = dist * 4 + 200
    return cam


# ----------------------------------------------------------------------------- lighting
def _world(name):
    w = bpy.data.worlds.new(name)
    w.use_nodes = True
    bpy.context.scene.world = w
    return w, w.node_tree


def studio_lighting(sc, extent):
    """Neutral grey studio: soft key from front-left, fill, rim; mid-grey world."""
    w, nt = _world("Studio")
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (0.42, 0.42, 0.42, 1)
    bg.inputs["Strength"].default_value = 0.55
    key = bpy.data.lights.new("Key", "SUN")
    key.energy = 3.2
    key.angle = math.radians(8)
    k = bpy.data.objects.new("Key", key)
    k.rotation_euler = (math.radians(50), 0, math.radians(-35))
    sc.collection.objects.link(k)
    rim = bpy.data.lights.new("Rim", "SUN")
    rim.energy = 1.2
    rim.angle = math.radians(15)
    r = bpy.data.objects.new("Rim", rim)
    r.rotation_euler = (math.radians(60), 0, math.radians(160))
    sc.collection.objects.link(r)
    # ground: neutral grey disc ("turntable") on an infinite-looking floor
    size = max(extent * 6, 30)
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Floor"
    floor.data.materials.append(mats.flat("Floor", (0.3, 0.3, 0.3), 0.85))
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=extent * 0.62, depth=0.04, location=(0, 0, -0.018))
    disc = bpy.context.active_object
    disc.name = "Turntable"
    disc.data.materials.append(mats.flat("TurntableMat", (0.22, 0.22, 0.22), 0.7))
    return [floor, disc]


def overcast_lighting(sc, ground_size=400):
    """Overcast Nordic sky: bright grey-blue dome brighter at the horizon-zenith band,
    weak diffuse sun (angle 30 deg) for soft shading; mossy heath ground."""
    w, nt = _world("Overcast")
    nodes, links = nt.nodes, nt.links
    bg = nodes["Background"]
    tc = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    ramp = nodes.new("ShaderNodeValToRGB")
    links.new(tc.outputs["Generated"], sep.inputs[0])
    links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    cr = ramp.color_ramp
    cr.elements[0].position = 0.0
    cr.elements[0].color = (0.30, 0.31, 0.30, 1)       # below horizon (ground bounce)
    cr.elements[1].position = 1.0
    cr.elements[1].color = (0.55, 0.60, 0.68, 1)       # zenith, cool grey-blue
    e = cr.elements.new(0.5)
    e.color = (0.80, 0.82, 0.84, 1)                    # bright hazy horizon
    e2 = cr.elements.new(0.62)
    e2.color = (0.74, 0.77, 0.80, 1)
    links.new(ramp.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 1.6
    sun = bpy.data.lights.new("SoftSun", "SUN")
    sun.energy = 0.9
    sun.angle = math.radians(30)
    sun.color = (1.0, 0.97, 0.93)
    so = bpy.data.objects.new("SoftSun", sun)
    so.rotation_euler = (math.radians(62), 0, math.radians(-40))
    sc.collection.objects.link(so)
    bpy.ops.mesh.primitive_plane_add(size=ground_size, location=(0, 0, 0))
    g = bpy.context.active_object
    g.name = "Heath"
    m = bpy.data.materials.new("Heath")
    m.use_nodes = True
    t = m.node_tree
    b = t.nodes["Principled BSDF"]
    n1 = t.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.35
    n1.inputs["Detail"].default_value = 8
    r2 = t.nodes.new("ShaderNodeValToRGB")
    r2.color_ramp.elements[0].color = (0.055, 0.065, 0.035, 1)
    r2.color_ramp.elements[1].color = (0.13, 0.13, 0.07, 1)
    t.links.new(n1.outputs["Fac"], r2.inputs["Fac"])
    t.links.new(r2.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    g.data.materials.append(m)
    return g


def render(sc, path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def render_sheet(sc, panels, path, res=(1280, 720)):
    """Render several camera panels side by side into one image (turntable-style sheet).
    panels: list of dicts(bmin, bmax, azimuth, elevation[, lens, target_z_frac])."""
    import os
    import tempfile
    from . import tex
    w = res[0] // len(panels)
    sc.render.resolution_x, sc.render.resolution_y = w, res[1]
    tiles = []
    tmpdir = tempfile.mkdtemp(prefix="sheet_")
    for i, p in enumerate(panels):
        cam = camera_fit(sc, p["bmin"], p["bmax"], azimuth_deg=p["azimuth"], elevation_deg=p["elevation"],
                         lens=p.get("lens", 50), target_z_frac=p.get("target_z_frac", 0.5),
                         margin=p.get("margin", 1.08))
        f = os.path.join(tmpdir, f"p{i}.png")
        render(sc, f)
        img = bpy.data.images.load(f)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)[..., :3]
        bpy.data.images.remove(img)
        tiles.append(px)
        bpy.data.objects.remove(cam)
        if i < len(panels) - 1:   # 2 px separator
            tiles.append(np.full((res[1], 2, 3), 0.15, np.float32))
    sheet = np.concatenate(tiles, axis=1)
    if sheet.shape[1] < res[0]:
        sheet = np.concatenate([sheet, np.full((res[1], res[0] - sheet.shape[1], 3), 0.15, np.float32)], 1)
    tex.save_png(path, sheet[:, :res[0]])
    sc.render.resolution_x, sc.render.resolution_y = res
    return path
