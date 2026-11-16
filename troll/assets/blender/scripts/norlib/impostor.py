"""Cross-billboard impostor (alternative LOD2): the LOD0 tree is rendered orthographically
from two perpendicular sides into a 2-view atlas (albedo+alpha under a uniform white sky,
i.e. albedo x ambient occlusion, and a camera-space normal map that equals the tangent-space
normal of each billboard quad).  The billboard mesh is 2 crossed quads = 4 triangles."""
import math
import os

import bpy
import numpy as np
from mathutils import Vector

from . import geo, mats, tex


def _load_rgba(path):
    img = bpy.data.images.load(path)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
    bpy.data.images.remove(img)
    return px


def _normal_material(mat):
    m = mat.copy()
    m.name = mat.name + "_nrmpass"
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    if bsdf.inputs["Normal"].links:
        nsock = bsdf.inputs["Normal"].links[0].from_socket
    else:
        nsock = nt.nodes.new("ShaderNodeNewGeometry").outputs["Normal"]
    vt = nt.nodes.new("ShaderNodeVectorTransform")
    vt.vector_type = "NORMAL"
    vt.convert_from = "WORLD"
    vt.convert_to = "CAMERA"
    nt.links.new(nsock, vt.inputs["Vector"])
    ma = nt.nodes.new("ShaderNodeVectorMath")
    ma.operation = "MULTIPLY_ADD"
    ma.inputs[1].default_value = (0.5, 0.5, -0.5)   # camera looks down -Z: flip Z so +Z faces viewer
    ma.inputs[2].default_value = (0.5, 0.5, 0.5)
    nt.links.new(vt.outputs["Vector"], ma.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(ma.outputs["Vector"], em.inputs["Color"])
    if bsdf.inputs["Alpha"].links:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(bsdf.inputs["Alpha"].links[0].from_socket, mix.inputs["Fac"])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(em.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs["Surface"])
    else:
        nt.links.new(em.outputs[0], out.inputs["Surface"])
    return m


def make_billboard(sc, objs, out_dir, base_name, prefix, samples=48, half_px=(256, 512)):
    """Renders the impostor atlas for `objs` (already in the scene, origin at trunk base)
    and returns (billboard_object, files dict).  Every other renderable object must be hidden."""
    co = []
    for o in objs:
        m = np.array(o.matrix_world)
        v = np.array([vv.co[:] for vv in o.data.vertices])
        co.append(v @ m[:3, :3].T + m[:3, 3])
    co = np.concatenate(co)
    hw = float(np.abs(co[:, :2]).max()) * 1.03
    Ht = float(co[:, 2].max()) * 1.01
    Hb = max(Ht, 4 * hw) * 1.03
    Wb = Hb / 2
    z0 = -0.015 * Hb        # transparent rows at both ends so wrap-around sampling stays clean

    prev = dict(engine=sc.render.engine, film=sc.render.film_transparent, vt=sc.view_settings.view_transform,
                look=sc.view_settings.look, x=sc.render.resolution_x, y=sc.render.resolution_y,
                world=sc.world, cmode=sc.render.image_settings.color_mode, samples=sc.cycles.samples)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.render.film_transparent = True
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.resolution_x, sc.render.resolution_y = half_px[0] * 2, half_px[1] * 2  # render 2x, downsample
    w = bpy.data.worlds.new("ImpostorWhite")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (1, 1, 1, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    sc.world = w
    lights = [o for o in sc.objects if o.type == "LIGHT" and not o.hide_render]
    for l in lights:
        l.hide_render = True

    cam_data = bpy.data.cameras.new("ImpCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = Hb
    cam = bpy.data.objects.new("ImpCam", cam_data)
    sc.collection.objects.link(cam)
    sc.camera = cam
    views = [(Vector((0, -200, z0 + Hb / 2)), Vector((0, 1, 0))), (Vector((200, 0, z0 + Hb / 2)), Vector((-1, 0, 0)))]
    tmp = bpy.app.tempdir or "/tmp"
    alb_tiles, nrm_tiles = [], []
    orig_mats = {o.name: o.data.materials[0] for o in objs}
    nmats = {name: _normal_material(m) for name, m in orig_mats.items()}
    for vi, (loc, fwd) in enumerate(views):
        cam.location = loc
        cam.rotation_mode = "QUATERNION"
        cam.rotation_quaternion = fwd.to_track_quat("-Z", "Y")
        cam_data.clip_end = 1000
        # albedo x AO pass
        sc.view_settings.view_transform = "Standard"
        sc.view_settings.look = "None"
        f = os.path.join(tmp, f"imp_alb_{vi}.png")
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        alb_tiles.append(_load_rgba(f))
        # normal pass (raw data)
        for o in objs:
            o.data.materials[0] = nmats[o.name]
        sc.view_settings.view_transform = "Raw"
        f = os.path.join(tmp, f"imp_nrm_{vi}.png")
        sc.render.filepath = f
        bpy.ops.render.render(write_still=True)
        nrm_tiles.append(_load_rgba(f))
        for o in objs:
            o.data.materials[0] = orig_mats[o.name]

    alb = np.concatenate(alb_tiles, axis=1)
    nrm = np.concatenate(nrm_tiles, axis=1)
    alpha = tex.downsample2(alb[..., 3])
    rgb = tex.downsample2(alb[..., :3] * alb[..., 3:4]) / np.maximum(alpha, 1e-4)[..., None]
    # the white-sky pass bakes ambient occlusion into the albedo; lift it so that the engine's
    # own lighting does not darken the billboard twice (linear-space gain)
    lin = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4) * 1.45
    rgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(np.clip(lin, 0.0031308, None), 1 / 2.4) - 0.055)
    rgb = tex.bleed_colour(np.clip(rgb, 0, 1), alpha)
    n3 = tex.downsample2(nrm[..., :3] * 2 - 1)
    n3 /= np.maximum(np.linalg.norm(n3, axis=2, keepdims=True), 1e-6)
    n3 = n3 * 0.5 + 0.5
    n3[alpha < 0.02] = (0.5, 0.5, 1.0)
    files = {"albedo": f"{base_name}_albedo.png", "normal": f"{base_name}_normal.png",
             "rough": f"{base_name}_rough.png"}
    tex.save_png(os.path.join(out_dir, files["albedo"]), np.dstack([rgb, alpha]))
    tex.save_png(os.path.join(out_dir, files["normal"]), n3)
    tex.save_png(os.path.join(out_dir, files["rough"]), np.full((64, 64), 0.85, np.float32))

    # restore scene
    bpy.data.objects.remove(cam)
    for l in lights:
        l.hide_render = False
    for m in nmats.values():
        bpy.data.materials.remove(m)
    sc.render.engine = prev["engine"]
    sc.render.film_transparent = prev["film"]
    sc.view_settings.view_transform = prev["vt"]
    sc.view_settings.look = prev["look"]
    sc.render.resolution_x, sc.render.resolution_y = prev["x"], prev["y"]
    sc.world = prev["world"]
    sc.render.image_settings.color_mode = prev["cmode"]
    sc.cycles.samples = prev["samples"]

    mb = geo.MeshBuilder()
    up = np.array([0, 0, 1.0])
    # quad 0 in XZ plane facing -Y, quad 1 in YZ plane facing +X; card base at the bottom edge
    mb.add_card(np.array([0, 0, z0]), up, np.array([0, -1.0, 0]), Hb, Wb, (0.0, 0.5))
    mb.add_card(np.array([0, 0, z0]), up, np.array([1.0, 0, 0]), Hb, Wb, (0.5, 1.0))
    mat = mats.pbr(prefix + "_billboard", out_dir, files, alpha=True)
    ob = mb.to_object(prefix + "_LOD2_Billboard", mat)
    return ob, files
