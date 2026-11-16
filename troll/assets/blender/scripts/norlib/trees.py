"""Shared tree pipeline: skeleton data -> LOD meshes -> materials -> export -> render -> stats.

A species script supplies a `generate(rng, **params) -> Tree` function and a list of
variants; `run_species` does the rest."""
import math
import os
import sys
import time
from dataclasses import dataclass, field

import bpy
import numpy as np

from . import bark, foliage, geo, impostor, mats, paths, studio
from . import export as ex

# Roblox-oriented budgets (total triangles per LOD; bark + foliage MeshParts)
LOD_CFG = {
    0: dict(tri_budget=10000, bark_frac=0.25, trunk_sides=12, branch_sides={1: 4, 2: 3, 3: 3}, step={0: 1, 1: 1, 2: 2, 3: 2},
            max_level=3, min_radius=0.0, card_segs=2, max_scale=1.0, mobile=False),
    1: dict(tri_budget=2500, bark_frac=0.25, trunk_sides=7, branch_sides={1: 3, 2: 3, 3: 3}, step={0: 2, 1: 3, 2: 4, 3: 4},
            max_level=1, min_radius=0.03, card_segs=1, max_scale=1.7, mobile=True),
    2: dict(tri_budget=500, bark_frac=0.15, trunk_sides=4, branch_sides={1: 3, 2: 3, 3: 3}, step={0: 4, 1: 99, 2: 99, 3: 99},
            max_level=1, min_radius=0.07, card_segs=1, max_scale=2.6, mobile=True),
}


@dataclass
class Tube:
    pts: np.ndarray
    radii: np.ndarray
    level: int                       # 0 trunk, 1 limb, 2 branch, 3 twig
    u_range: tuple = (0.5, 1.0)      # bark atlas half
    v0: float = 0.0
    flare: object = None
    cap: bool = True


@dataclass
class Card:
    base: np.ndarray
    direction: np.ndarray
    normal: np.ndarray
    length: float
    width: float
    variant: int = 0
    bend: float = 0.0
    importance: float = 1.0
    outward: np.ndarray = None
    fold: float = 0.0


@dataclass
class Tree:
    tubes: list = field(default_factory=list)
    cards: list = field(default_factory=list)
    info: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- helpers
def resample_idx(n, step):
    if step >= n - 1:
        return [0, n - 1]
    idx = list(range(0, n, step))
    if idx[-1] != n - 1:
        idx.append(n - 1)
    return idx


def outward_dir(p, axis_xy, up_mix=0.6):
    d = np.array([p[0] - axis_xy[0], p[1] - axis_xy[1], 0.0])
    if np.linalg.norm(d) < 1e-6:
        d = np.array([0, 0, 1.0])
    d = geo.unit(d) + np.array([0, 0, up_mix])
    return geo.unit(d)


def stratified(cards, n, bins=14):
    """Pick n cards keeping the vertical distribution of foliage area (so reduced LODs do
    not lose the crown top), best importance first inside each height band."""
    if n >= len(cards):
        return list(cards)
    fixed = [c for c in cards if c.importance >= 99]
    rest = [c for c in cards if c.importance < 99]
    n_rest = max(n - len(fixed), 0)
    z = np.array([c.base[2] for c in rest])
    area = np.array([c.length * c.width for c in rest])
    edges = np.linspace(z.min(), z.max() + 1e-6, bins + 1)
    band = np.clip(np.searchsorted(edges, z, side="right") - 1, 0, bins - 1)
    share = np.array([area[band == b].sum() for b in range(bins)])
    quota = np.floor(share / share.sum() * n_rest).astype(int)
    while quota.sum() < n_rest:
        quota[np.argmax(share / share.sum() * n_rest - quota)] += 1
    out = list(fixed)
    for b in range(bins):
        members = [rest[i] for i in np.nonzero(band == b)[0]]   # already importance-sorted
        out += members[:quota[b]]
    return out[:n]


def build_lod(tree, lod, bark_mat, fol_mat, prefix):
    cfg = LOD_CFG[lod]
    mb = geo.MeshBuilder()
    bark_budget = cfg["tri_budget"] * tree.info.get("bark_frac", {}).get(lod, cfg["bark_frac"])
    # trunk first, then limbs by decreasing radius until the bark share of the budget is used
    order = sorted(tree.tubes, key=lambda t: (t.level > 0, -float(t.radii[0])))
    for t in order:
        if t.level > cfg["max_level"]:
            continue
        if t.level > 0 and (t.radii[0] < cfg["min_radius"] or mb.tris > bark_budget):
            continue
        idx = resample_idx(len(t.pts), cfg["step"].get(t.level, 1))
        if len(idx) < 2:
            continue
        sides = cfg["trunk_sides"] if t.level == 0 else cfg["branch_sides"].get(t.level, 3)
        flare = None
        if t.flare is not None and lod == 0:
            fl = t.flare
            flare = lambda i, a, idx=idx, fl=fl: fl(idx[i], a)
        mb.add_tube(t.pts[idx], t.radii[idx], sides, t.u_range, v0=t.v0, cap_end=t.cap and lod == 0,
                    flare=flare)
    bark_tris = mb.tris
    left = max(cfg["tri_budget"] - bark_tris, 0)
    cards = sorted(tree.cards, key=lambda c: -c.importance)
    # first pass: how many cards fit if every card is a single quad
    n = min(len(cards), left // 2)
    scale = 1.0
    if lod > 0 and n > 0:
        scale = min(math.sqrt(len(cards) / n), cfg["max_scale"])
    keep = stratified(cards, n)
    # LOD0: spend leftover triangles on bending the biggest cards (2 segments = 4 tris)
    extra = (left - 2 * n) // 2 if cfg["card_segs"] > 1 else 0
    fb = geo.MeshBuilder()
    for c in keep:
        u = (0.0, 0.5) if c.variant == 0 else (0.5, 1.0)
        sc_ = 1.0 if c.importance >= 99 else scale     # leader / fixed cards keep their size
        top = tree.info.get("height")
        if top and sc_ > 1.0:                          # never let up-scaled cards poke above the tree
            rise = geo.unit(c.direction)[2] * c.length
            if rise > 1e-3:
                sc_ = max(1.0, min(sc_, (top - 0.3 - c.base[2]) / rise))
        segs = 1
        if extra > 0 and c.length > 0.75:
            segs, extra = 2, extra - 1
        fb.add_card(c.base, c.direction, c.normal, c.length * sc_, c.width * sc_, u,
                    bend=c.bend if segs > 1 else c.bend * 0.5, segs=segs,
                    outward=c.outward, outward_mix=0.55)
    objs = [mb.to_object(f"{prefix}_LOD{lod}_Bark", bark_mat)]
    if fb.faces:
        objs.append(fb.to_object(f"{prefix}_LOD{lod}_Foliage", fol_mat))
    return objs, {"cards_total": len(cards), "cards_kept": n, "card_scale": round(scale, 3)}


def species_materials(species, force=False):
    full = paths.tex_dir(species)
    mob = paths.tex_dir(species, mobile=True)
    need = force or not os.path.exists(os.path.join(full, f"{species}_foliage_albedo.png"))
    t0 = time.time()
    if need:
        bark.build_atlas(species, full, mob)
        foliage.build_atlas(species, full, mob)
    bf = {k: f"{species}_bark_{k}.png" for k in ("albedo", "normal", "rough")}
    ff = {k: f"{species}_foliage_{k}.png" for k in ("albedo", "normal", "rough")}
    m = {
        "bark": mats.pbr(f"{species}_bark", full, bf),
        "foliage": mats.pbr(f"{species}_foliage", full, ff, alpha=True),
        "bark_mobile": mats.pbr(f"{species}_bark_mobile", mob, bf),
        "foliage_mobile": mats.pbr(f"{species}_foliage_mobile", mob, ff, alpha=True),
    }
    print(f"[{species}] textures ready ({'built' if need else 'cached'}) {time.time() - t0:.1f}s")
    return m


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opts = {"only": None, "render": True, "force_tex": False, "samples": 64}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--only":
            opts["only"] = argv[i + 1].split(","); i += 1
        elif a == "--no-render":
            opts["render"] = False
        elif a == "--force-tex":
            opts["force_tex"] = True
        elif a == "--samples":
            opts["samples"] = int(argv[i + 1]); i += 1
        i += 1
    return opts


def run_species(species, variants, generate):
    """variants: list of dicts with keys asset, label, seed, params."""
    opts = parse_args()
    first = True
    for var in variants:
        if opts["only"] and var["asset"] not in opts["only"]:
            continue
        t0 = time.time()
        sc = studio.reset()
        m = species_materials(species, force=opts["force_tex"] and first)
        first = False
        rng = np.random.default_rng(var["seed"])
        tree = generate(rng, **var["params"])
        prefix = var["label"]
        out = paths.export_dir(var["asset"])
        record = {"asset": var["asset"], "species": species, "seed": var["seed"], "params": var["params"],
                  "blender": bpy.app.version_string, "lods": {}, "info": tree.info,
                  "textures": {"folder": os.path.relpath(paths.tex_dir(species), paths.ROOT),
                               "mobile_folder": os.path.relpath(paths.tex_dir(species, True), paths.ROOT)}}
        lod_objs = {}
        for lod in (0, 1, 2):
            mob = LOD_CFG[lod]["mobile"]
            objs, cinfo = build_lod(tree, lod, m["bark_mobile" if mob else "bark"],
                                    m["foliage_mobile" if mob else "foliage"], prefix)
            st = ex.export_lod(objs, out, f"{var['asset']}_LOD{lod}")
            st.update(cinfo)
            st["texture_px"] = 512 if mob else 1024
            bmin, bmax = ex.bounds(objs)
            st["height_m"] = round(float(bmax[2] - bmin[2]), 2)
            st["width_x_m"] = round(float(bmax[0] - bmin[0]), 2)
            st["width_y_m"] = round(float(bmax[1] - bmin[1]), 2)
            record["lods"][lod] = st
            lod_objs[lod] = objs
            print(f"[{var['asset']}] LOD{lod}: {st['tris']} tris, {st['verts']} verts, h={st['height_m']} m")
        # alternative LOD2: cross-billboard impostor rendered from LOD0
        for lod in (1, 2):
            for o in lod_objs[lod]:
                o.hide_render = True
        bb, bb_files = impostor.make_billboard(sc, lod_objs[0], paths.tex_dir(species, True),
                                               f"{var['asset']}_impostor", prefix)
        st = ex.export_lod([bb], out, f"{var['asset']}_LOD2_billboard")
        st.update({"texture_px": 512, "textures": bb_files})
        bmin, bmax = ex.bounds([bb])
        st["height_m"] = round(float(bmax[2] - bmin[2]), 2)
        st["width_x_m"] = round(float(bmax[0] - bmin[0]), 2)
        st["width_y_m"] = round(float(bmax[1] - bmin[1]), 2)
        record["lods"]["2_billboard"] = st
        lod_objs[3] = [bb]
        for lod in (1, 2):
            for o in lod_objs[lod]:
                o.hide_render = False
        if opts["render"]:
            # LOD comparison image: LOD0 | LOD1 | LOD2 side by side
            span = max(record["lods"][0]["width_x_m"], record["lods"][0]["width_y_m"]) * 1.05
            for lod in (1, 2, 3):
                for o in lod_objs[lod]:
                    o.location.x += span * lod
            studio.cycles(sc, opts["samples"], (1280, 720))
            l0 = lod_objs[0]
            bmin, bmax = ex.bounds(l0)
            extent = float(max(bmax[0] - bmin[0], bmax[1] - bmin[1]))
            for lod in (1, 2, 3):
                for o in lod_objs[lod]:
                    o.hide_render = True
            hum = studio.human(loc=(bmax[0] + 1.0, bmin[1] + (bmax[1] - bmin[1]) * 0.35, 0))
            studio_objs = studio.studio_lighting(sc, extent)
            ren = paths.ensure(paths.RENDERS)
            t1 = time.time()
            H = float(bmax[2])
            close_h = min(H, max(4.0, H * 0.3))
            panels = [
                dict(bmin=[bmin[0], bmin[1], 0], bmax=[bmax[0] + 1.6, bmax[1], bmax[2]],
                     azimuth=-20, elevation=4),
                dict(bmin=[bmin[0], bmin[1], 0], bmax=[bmax[0], bmax[1], bmax[2]],
                     azimuth=70, elevation=4),
                dict(bmin=[bmin[0] * 0.5, bmin[1] * 0.5, 0], bmax=[bmax[0] + 1.6, bmax[1] * 0.5, close_h],
                     azimuth=25, elevation=10, margin=1.02),
            ]
            studio.render_sheet(sc, panels, os.path.join(ren, f"{var['asset']}.png"))
            record["render_seconds"] = round(time.time() - t1, 1)
            if var.get("lod_render", False):
                for lod in (1, 2, 3):
                    for o in lod_objs[lod]:
                        o.hide_render = False
                for o in studio_objs:
                    o.scale = (3, 3, 1)
                studio.camera_fit(sc, [bmin[0], bmin[1], 0], [bmax[0] + 3 * span + 1.8, bmax[1], bmax[2]],
                                  azimuth_deg=0, elevation_deg=3, lens=50)
                studio.render(sc, os.path.join(ren, f"{var['asset']}_lods.png"))
        # small .blend for inspection (kept only if < 20 MB)
        bdir = paths.ensure(paths.BLEND)
        bpath = os.path.join(bdir, f"{var['asset']}.blend")
        bpy.ops.wm.save_as_mainfile(filepath=bpath, compress=True, relative_remap=True)
        if os.path.getsize(bpath) > 20 * 1024 * 1024:
            os.remove(bpath)
            record["blend"] = None
        else:
            record["blend"] = os.path.relpath(bpath, paths.ROOT)
        for f in os.listdir(bdir):
            if f.endswith(".blend1"):
                os.remove(os.path.join(bdir, f))
        record["build_seconds"] = round(time.time() - t0, 1)
        ex.write_stats(os.path.join(paths.STATS, f"{var['asset']}.json"), record)
        print(f"[{var['asset']}] done in {record['build_seconds']} s")
