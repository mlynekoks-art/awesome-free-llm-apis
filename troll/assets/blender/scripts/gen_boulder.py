"""Granite / gneiss boulders (glacially rounded erratics), 0.5 m, 1.5 m and 4 m.

Pipeline: high-poly sculpt (icosphere + noise + soft joint-plane facets, flattened,
partly buried base) with a procedural granite/gneiss + lichen + moss shader ->
decimated low-poly LOD0 (<= 1,500 tris) with Smart-UV -> Cycles bake (selected-to-active)
of albedo, tangent-space normal and roughness to 1024 px PNG -> LOD1/LOD2 decimated
from LOD0 (UVs preserved, 512 px textures).

Run:  blender -b -P gen_boulder.py -- [--only boulder_150] [--no-render]
"""
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import noise, Vector  # noqa: E402
from norlib import export as ex, mats, paths, studio, tex, trees  # noqa: E402

VARIANTS = [
    dict(asset="boulder_050", label="Boulder_050", seed=7, size=0.5, subdiv=6, gneiss=0.0, moss=0.25, lichen=0.6,
         facets=3, flat=0.55),
    dict(asset="boulder_150", label="Boulder_150", seed=19, size=1.5, subdiv=7, gneiss=0.6, moss=0.45, lichen=0.8,
         facets=4, flat=0.6),
    dict(asset="boulder_400", label="Boulder_400", seed=31, size=4.0, subdiv=7, gneiss=0.25, moss=0.7, lichen=1.0,
         facets=5, flat=0.65),
]
LOD_TRIS = {0: 1500, 1: 500, 2: 150}


# ----------------------------------------------------------------------------- sculpt
def fbm3(p, octaves, seed_off):
    return noise.fractal(Vector(p) + Vector((seed_off, seed_off * 0.7, seed_off * 1.3)), 0.5, 2.0, octaves,
                         noise_basis="PERLIN_NEW")


def sculpt(rng, size, subdiv, facets, flat, name):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=1.0)
    ob = bpy.context.active_object
    ob.name = name + "_high"
    me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get("co", co)
    p = co.reshape(-1, 3).astype(np.float64)
    so = rng.uniform(0, 100)
    r = np.empty(n)
    for i in range(n):
        v = p[i]
        r[i] = (1.0 + 0.2 * fbm3(v * 0.9, 3, so) + 0.03 * fbm3(v * 2.8, 4, so + 11)
                + 0.005 * fbm3(v * 9.0, 3, so + 23))
    q = p * r[:, None]
    # soft joint planes -> blocky but glacially rounded facets
    for k in range(facets):
        nk = rng.normal(size=3)
        nk[2] *= 0.6
        nk /= np.linalg.norm(nk)
        d = rng.uniform(0.62, 0.85)
        s = 0.12
        dist = q @ nk - d
        soft = s * np.log1p(np.exp(dist / s))          # softplus: rounds the edge
        q -= nk[None, :] * soft[:, None] * 0.92
    a = size / 2
    b = a * rng.uniform(0.62, 0.85)
    c = a * rng.uniform(0.5, 0.68)
    q *= np.array([a, b, c])
    # rotate around z for variety
    ang = rng.uniform(0, 6.28)
    rot = np.array([[math.cos(ang), -math.sin(ang), 0], [math.sin(ang), math.cos(ang), 0], [0, 0, 1]])
    q = q @ rot.T
    zmin = q[:, 2].min()
    zcut = zmin + (q[:, 2].max() - zmin) * (1 - flat) * 0.35
    below = q[:, 2] < zcut
    q[below, 2] = zcut - (zcut - q[below, 2]) * 0.25    # flattened base resting on the ground
    q[:, 2] -= q[:, 2].min() + 0.06 * (q[:, 2].max() - q[:, 2].min())  # ~6 % buried
    me.vertices.foreach_set("co", q.astype(np.float32).ravel())
    me.update()
    bpy.ops.object.shade_smooth()
    return ob


# ----------------------------------------------------------------------------- shader
def rock_material(name, size, gneiss, moss, lichen, seed):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    for x in list(N):
        N.remove(x)
    out = N.new("ShaderNodeOutputMaterial")
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    L.new(bsdf.outputs[0], out.inputs[0])
    tc = N.new("ShaderNodeTexCoord")
    geo_n = N.new("ShaderNodeNewGeometry")
    sep_n = N.new("ShaderNodeSeparateXYZ")
    L.new(geo_n.outputs["Normal"], sep_n.inputs[0])
    obj = tc.outputs["Object"]
    off = N.new("ShaderNodeVectorMath")
    off.operation = "ADD"
    off.inputs[1].default_value = (seed * 3.1, seed * 1.7, seed * 2.3)
    L.new(obj, off.inputs[0])
    P = off.outputs[0]

    def noise_t(scale, detail=6, rough=0.55, dist=0.0, dim="3D"):
        t = N.new("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = scale
        t.inputs["Detail"].default_value = detail
        t.inputs["Roughness"].default_value = rough
        t.inputs["Distortion"].default_value = dist
        L.new(P, t.inputs["Vector"])
        return t

    def ramp(fac, stops):
        r = N.new("ShaderNodeValToRGB")
        cr = r.color_ramp
        cr.elements[0].position, cr.elements[0].color = stops[0][0], (*stops[0][1], 1)
        cr.elements[1].position, cr.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
        for pos, col in stops[1:-1]:
            e = cr.elements.new(pos)
            e.color = (*col, 1)
        L.new(fac, r.inputs["Fac"])
        return r

    def mix(a, b, fac, blend="MIX"):
        mx = N.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.blend_type = blend
        L.new(fac, mx.inputs["Factor"])
        L.new(a, mx.inputs["A"])
        L.new(b, mx.inputs["B"])
        return mx.outputs["Result"]

    def mathn(op, a, b=None, val=None):
        mt = N.new("ShaderNodeMath")
        mt.operation = op
        if isinstance(a, float):
            mt.inputs[0].default_value = a
        else:
            L.new(a, mt.inputs[0])
        if b is not None:
            L.new(b, mt.inputs[1])
        elif val is not None:
            mt.inputs[1].default_value = val
        mt.use_clamp = True
        return mt.outputs[0]

    # base granite tone (linear albedo ~0.13-0.32)
    base = ramp(noise_t(1.2 / max(size, 0.6), 8, 0.6).outputs["Fac"],
                [(0.3, (0.13, 0.125, 0.12)), (0.5, (0.22, 0.21, 0.2)), (0.7, (0.30, 0.285, 0.27))])
    col = base.outputs["Color"]
    # gneiss banding
    wave = N.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 2.2 / max(size, 0.6)
    wave.inputs["Distortion"].default_value = 9
    wave.inputs["Detail"].default_value = 6
    wave.bands_direction = "Z"
    L.new(P, wave.inputs["Vector"])
    band = ramp(wave.outputs["Fac"], [(0.35, (0.1, 0.095, 0.09)), (0.65, (0.34, 0.31, 0.29))])
    gfac = N.new("ShaderNodeValue")
    gfac.outputs[0].default_value = gneiss * 0.55
    col = mix(col, band.outputs["Color"], gfac.outputs[0])
    # mineral speckles: mica (black), feldspar (pink), quartz (white)
    vor = N.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 140.0
    L.new(P, vor.inputs["Vector"])
    vsep = N.new("ShaderNodeSeparateColor")
    L.new(vor.outputs["Color"], vsep.inputs[0])
    mica = mathn("MULTIPLY", mathn("GREATER_THAN", vsep.outputs[0], val=0.86), val=0.6)
    feld = mathn("MULTIPLY", mathn("LESS_THAN", vsep.outputs[1], val=0.1), val=0.35)
    quartz = mathn("MULTIPLY", mathn("GREATER_THAN", vsep.outputs[2], val=0.92), val=0.4)
    col = mix(col, ramp(vsep.outputs[0], [(0, (0.03, 0.03, 0.03)), (1, (0.05, 0.045, 0.04))]).outputs["Color"], mica)
    col = mix(col, ramp(vsep.outputs[1], [(0, (0.36, 0.25, 0.21)), (1, (0.3, 0.22, 0.2))]).outputs["Color"], feld)
    col = mix(col, ramp(vsep.outputs[2], [(0, (0.42, 0.42, 0.40)), (1, (0.5, 0.5, 0.48))]).outputs["Color"], quartz)
    # weathering stains, vertical streaks
    streak = N.new("ShaderNodeMapping")
    streak.inputs["Scale"].default_value = (6.0, 6.0, 0.6)
    L.new(P, streak.inputs["Vector"])
    st = N.new("ShaderNodeTexNoise")
    st.inputs["Scale"].default_value = 1.5 / max(size, 0.6)
    st.inputs["Detail"].default_value = 4
    L.new(streak.outputs[0], st.inputs["Vector"])
    stain = ramp(st.outputs["Fac"], [(0.45, (1, 1, 1)), (0.7, (0.62, 0.6, 0.55))])
    col = mix(col, stain.outputs["Color"], mathn("ADD", 1.0, val=0.0), "MULTIPLY")
    # crustose lichens: pale grey-green patches + yellow-green map lichen
    up_ok = mathn("GREATER_THAN", sep_n.outputs["Z"], val=-0.35)
    l1 = noise_t(4.0, 5, 0.7, 0.4)
    l1m = mathn("MULTIPLY", ramp(l1.outputs["Fac"], [(0.52, (0, 0, 0)), (0.58, (1, 1, 1))]).outputs["Color"], up_ok)
    l1m = mathn("MULTIPLY", l1m, val=lichen)
    lcol = ramp(noise_t(30, 3).outputs["Fac"], [(0.3, (0.27, 0.285, 0.24)), (0.7, (0.36, 0.37, 0.32))])
    col = mix(col, lcol.outputs["Color"], l1m)
    l2 = noise_t(7.0, 4, 0.7, 0.8)
    l2m = mathn("MULTIPLY", ramp(l2.outputs["Fac"], [(0.64, (0, 0, 0)), (0.68, (1, 1, 1))]).outputs["Color"], up_ok)
    l2m = mathn("MULTIPLY", l2m, val=lichen)
    l2col = ramp(noise_t(50, 2).outputs["Fac"], [(0.4, (0.24, 0.27, 0.05)), (0.6, (0.32, 0.34, 0.09))])
    col = mix(col, l2col.outputs["Color"], l2m)
    # black rim lichen dots
    l3m = mathn("MULTIPLY", ramp(noise_t(25, 2).outputs["Fac"], [(0.7, (0, 0, 0)), (0.74, (1, 1, 1))]).outputs["Color"],
                val=lichen * 0.6)
    col = mix(col, ramp(l1.outputs["Fac"], [(0, (0.03, 0.03, 0.025)), (1, (0.05, 0.05, 0.04))]).outputs["Color"], l3m)
    # moss on the top and near the ground
    topm = ramp(sep_n.outputs["Z"], [(0.45, (0, 0, 0)), (0.8, (1, 1, 1))]).outputs["Color"]
    mn = noise_t(2.2 / max(size, 0.6), 6, 0.65, 0.5)
    mmask = mathn("MULTIPLY", topm, ramp(mn.outputs["Fac"], [(0.42, (0, 0, 0)), (0.52, (1, 1, 1))]).outputs["Color"])
    sepz = N.new("ShaderNodeSeparateXYZ")
    L.new(obj, sepz.inputs[0])
    ground = ramp(sepz.outputs["Z"], [(0.0, (1, 1, 1)), (0.06 * size + 0.02, (0, 0, 0))]).outputs["Color"]
    mmask = mathn("MAXIMUM", mmask, mathn("MULTIPLY", ground, val=0.8))
    mmask = mathn("MULTIPLY", mmask, val=moss)
    mcol = ramp(noise_t(18, 4).outputs["Fac"], [(0.3, (0.035, 0.06, 0.012)), (0.55, (0.07, 0.1, 0.02)),
                                                (0.8, (0.12, 0.12, 0.04))])
    col = mix(col, mcol.outputs["Color"], mmask)
    # cavity darkening
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.08 * size
    ao.samples = 8
    aor = ramp(ao.outputs["AO"], [(0.0, (0.55, 0.55, 0.55)), (1.0, (1, 1, 1))])
    col = mix(col, aor.outputs["Color"], mathn("ADD", 1.0, val=0.0), "MULTIPLY")
    L.new(col, bsdf.inputs["Base Color"])
    # roughness
    rough = mathn("ADD", mathn("MULTIPLY", l1m, val=0.12), mathn("MULTIPLY", mmask, val=0.2))
    rough = mathn("ADD", rough, val=0.72)
    L.new(rough, bsdf.inputs["Roughness"])
    # micro relief for the normal bake
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.004
    hmix = mathn("ADD", noise_t(40, 6, 0.6).outputs["Fac"], mathn("MULTIPLY", l1m, val=0.4))
    hmix = mathn("ADD", hmix, mathn("MULTIPLY", mmask, val=0.8))
    L.new(hmix, bump.inputs["Height"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


# ----------------------------------------------------------------------------- bake
def decimate_to(ob, tris):
    me = ob.data
    me.calc_loop_triangles()
    cur = len(me.loop_triangles)
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = min(1.0, tris / cur)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier=mod.name)
    # nudge to the exact budget if the collapse overshoots
    for _ in range(4):
        ob.data.calc_loop_triangles()
        cur = len(ob.data.loop_triangles)
        if cur <= tris:
            break
        mod = ob.modifiers.new("dec", "DECIMATE")
        mod.ratio = tris / cur * 0.995
        bpy.ops.object.modifier_apply(modifier=mod.name)


def bake(sc, high, low, img, btype, cage):
    mat = low.data.materials[0]
    nt = mat.node_tree
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = img
    nt.nodes.active = node
    bpy.ops.object.select_all(action="DESELECT")
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    kw = dict(type=btype, use_selected_to_active=True, cage_extrusion=cage, max_ray_distance=cage * 3,
              margin=12, margin_type="EXTEND")
    if btype == "DIFFUSE":
        kw["pass_filter"] = {"COLOR"}
    if btype == "NORMAL":
        kw["normal_space"] = "TANGENT"
    bpy.ops.object.bake(**kw)
    nt.nodes.remove(node)


def img_to_array(img):
    w, h = img.size
    return np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)


def build(var, opts):
    t0 = time.time()
    sc = studio.reset()
    rng = np.random.default_rng(var["seed"])
    size = var["size"]
    high = sculpt(rng, size, var["subdiv"], var["facets"], var["flat"], var["label"])
    high.data.materials.append(rock_material(var["label"] + "_procedural", size, var["gneiss"], var["moss"],
                                             var["lichen"], var["seed"]))
    # LOD0 low poly
    low = high.copy()
    low.data = high.data.copy()
    low.name = var["label"] + "_LOD0"
    sc.collection.objects.link(low)
    low.data.materials.clear()
    decimate_to(low, LOD_TRIS[0])
    bpy.ops.object.select_all(action="DESELECT")
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.008, area_weight=0.0,
                             scale_to_bounds=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()
    tmpmat = bpy.data.materials.new("bake_target")
    tmpmat.use_nodes = True
    low.data.materials.append(tmpmat)
    # bake
    studio.cycles(sc, 8, (64, 64))
    sc.cycles.use_denoising = False
    full = paths.tex_dir("boulder")
    mob = paths.tex_dir("boulder", True)
    files = {}
    cage = 0.04 * size
    for key, btype, noncolor, samples in (("albedo", "DIFFUSE", False, 4), ("normal", "NORMAL", True, 8),
                                         ("rough", "ROUGHNESS", True, 2)):
        sc.cycles.samples = samples
        img = bpy.data.images.new(f"{var['asset']}_{key}", 1024, 1024, alpha=False, float_buffer=False)
        if noncolor:
            img.colorspace_settings.name = "Non-Color"
        bake(sc, high, low, img, btype, cage)
        arr = img_to_array(img)[..., :3]
        if key == "rough":
            arr = arr[..., :1]
        name = f"{var['asset']}_{key}.png"
        tex.save_png(os.path.join(full, name), arr)
        half = tex.downsample2(arr)
        if key == "normal":
            n3 = half * 2 - 1
            n3 /= np.maximum(np.linalg.norm(n3, axis=2, keepdims=True), 1e-6)
            half = n3 * 0.5 + 0.5
        tex.save_png(os.path.join(mob, name), half)
        files[key] = name
    tex.save_png(os.path.join(full, "boulder_metalness.png"), np.zeros((64, 64)))
    bake_s = time.time() - t0
    m_full = mats.pbr(var["label"] + "_rock", full, files)
    m_mob = mats.pbr(var["label"] + "_rock_mobile", mob, files)
    low.data.materials.clear()
    low.data.materials.append(m_full)
    lods = {0: low}
    for lod in (1, 2):
        o = low.copy()
        o.data = low.data.copy()
        o.name = f"{var['label']}_LOD{lod}"
        sc.collection.objects.link(o)
        decimate_to(o, LOD_TRIS[lod])
        o.data.materials.clear()
        o.data.materials.append(m_mob)
        lods[lod] = o
    high.hide_render = True
    high.hide_set(True)
    out = paths.export_dir(var["asset"])
    record = {"asset": var["asset"], "species": "boulder", "seed": var["seed"], "params": {
        k: var[k] for k in ("size", "subdiv", "gneiss", "moss", "lichen", "facets", "flat")},
        "blender": bpy.app.version_string, "lods": {},
        "high_poly_tris": len(high.data.polygons),
        "textures": {"folder": os.path.relpath(full, paths.ROOT), "mobile_folder": os.path.relpath(mob, paths.ROOT),
                     "files": files}, "bake_seconds": round(bake_s, 1)}
    for lod, o in lods.items():
        st = ex.export_lod([o], out, f"{var['asset']}_LOD{lod}")
        st["texture_px"] = 1024 if lod == 0 else 512
        bmin, bmax = ex.bounds([o])
        st["height_m"] = round(float(bmax[2]), 2)
        st["buried_m"] = round(float(-bmin[2]), 2)
        st["width_x_m"] = round(float(bmax[0] - bmin[0]), 2)
        st["width_y_m"] = round(float(bmax[1] - bmin[1]), 2)
        record["lods"][lod] = st
        print(f"[{var['asset']}] LOD{lod}: {st['tris']} tris, {st['verts']} verts")
    if opts["render"]:
        studio.cycles(sc, opts["samples"], (1280, 720))
        span = size * 1.3
        for lod in (1, 2):
            lods[lod].location.x += span * lod
            lods[lod].hide_render = True
        bmin, bmax = ex.bounds([low])
        studio.human(loc=(bmax[0] + 0.5, (bmin[1] + bmax[1]) / 2, 0))
        sobj = studio.studio_lighting(sc, max(size * 2.0, 3.0))
        studio.render_sheet(sc, [
            dict(bmin=[bmin[0], bmin[1], 0], bmax=[bmax[0] + 1.0, bmax[1], max(bmax[2], 1.85)], azimuth=-25, elevation=12),
            dict(bmin=list(bmin), bmax=[bmax[0] + 1.0, bmax[1], bmax[2]], azimuth=140, elevation=35, margin=1.1),
        ], os.path.join(paths.ensure(paths.RENDERS), f"{var['asset']}.png"))
        for lod in (1, 2):
            lods[lod].hide_render = False
        for o in sobj:
            o.scale = (2, 2, 1)
        cam = studio.camera_fit(sc, [bmin[0], bmin[1], 0], [bmax[0] + 2 * span + 0.8, bmax[1], max(bmax[2], 1.85)],
                                azimuth_deg=-10, elevation_deg=15)
        studio.render(sc, os.path.join(paths.RENDERS, f"{var['asset']}_lods.png"))
    bpy.data.objects.remove(high)
    bdir = paths.ensure(paths.BLEND)
    bpath = os.path.join(bdir, f"{var['asset']}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=bpath, compress=True, relative_remap=True)
    record["blend"] = os.path.relpath(bpath, paths.ROOT) if os.path.getsize(bpath) < 20 * 2 ** 20 else None
    if record["blend"] is None:
        os.remove(bpath)
    record["build_seconds"] = round(time.time() - t0, 1)
    ex.write_stats(os.path.join(paths.STATS, f"{var['asset']}.json"), record)
    print(f"[{var['asset']}] done in {record['build_seconds']} s")


if __name__ == "__main__":
    opts = trees.parse_args()
    for v in VARIANTS:
        if opts["only"] and v["asset"] not in opts["only"]:
            continue
        build(v, opts)
