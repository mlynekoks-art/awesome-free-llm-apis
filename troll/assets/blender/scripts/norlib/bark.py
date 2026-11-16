"""Bark texture atlases (1024x1024).

Layout: left half (u 0..0.5) = lower-trunk bark, right half (u 0.5..1) = upper trunk /
branch bark.  Each half is 512x1024 and tiles on its own in both directions, so a tube
whose ring u runs 0..0.5 (or 0.5..1) and whose v repeats freely shows no seam.
The tube builder (geo.add_tube) advances v by ds / (2 * circumference) so that the
texel aspect stays square on any trunk or branch radius.
"""
import numpy as np
from . import tex

HALF = (1024, 512)  # (H, W)


def _mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return a * (1 - t) + b * t


def _cellrand(cid, rng, n=None):
    n = n or int(cid.max()) + 1
    return rng.random(n)[cid]


def _plates(rng, cells, warp_px, warp_feat, jitter=0.95, aniso=1.0):
    wx = tex.fbm(HALF, warp_feat, rng, 3) * warp_px
    wy = tex.fbm(HALF, warp_feat, rng, 3) * warp_px
    f1, f2, cid = tex.worley(HALF, cells[0], cells[1], rng, jitter, warp=(wx, wy), aniso=aniso)
    return f1, f2, cid


# ----------------------------------------------------------------------------- spruce
def spruce_lower(rng):
    f1, f2, cid = _plates(rng, (15, 26), 9, 60)
    edge = np.clip((f2 - f1) / 9.0, 0, 1)
    tilt = _cellrand(cid, rng)
    yy = np.mgrid[0:HALF[0], 0:HALF[1]][0].astype(np.float32)
    plate = edge ** 0.5 * (0.6 + 0.4 * tilt) + 0.15 * tex.fbm(HALF, 6, rng, 3)
    hgt = plate * 5.0
    pal = np.array([tex.srgb(c) for c in [(106, 78, 62), (98, 84, 74), (92, 70, 58), (110, 88, 72), (96, 78, 66)]])
    col = pal[(_cellrand(cid, rng) * len(pal)).astype(int) % len(pal)]
    col = col * (0.8 + 0.3 * tex.norm01(tex.fbm(HALF, 20, rng, 4)))[..., None]
    crack = tex.srgb((44, 32, 26))
    col = _mix(crack, col, edge ** 0.6 * 1.4)
    lich = tex.norm01(tex.fbm(HALF, 90, rng, 4))
    col = _mix(col, tex.srgb((138, 140, 122)), np.clip((lich - 0.78) * 4, 0, 0.55) * edge)
    rough = 0.88 + 0.08 * (1 - edge)
    return col, hgt, rough


def spruce_upper(rng):
    f1, f2, cid = _plates(rng, (26, 44), 5, 40)
    edge = np.clip((f2 - f1) / 5.0, 0, 1)
    hgt = edge ** 0.5 * 2.0 + 0.3 * tex.fbm(HALF, 5, rng, 2)
    pal = np.array([tex.srgb(c) for c in [(124, 80, 58), (112, 86, 70), (134, 92, 66), (104, 76, 60)]])
    col = pal[(_cellrand(cid, rng) * len(pal)).astype(int) % len(pal)]
    col = col * (0.85 + 0.25 * tex.norm01(tex.fbm(HALF, 30, rng, 3)))[..., None]
    col = _mix(tex.srgb((70, 48, 38)), col, edge ** 0.5 * 1.3)
    return col, hgt, 0.8 + 0.1 * (1 - edge)


# ----------------------------------------------------------------------------- pine
def pine_lower(rng):
    f1, f2, cid = _plates(rng, (7, 5), 16, 120, aniso=0.45)
    edge = np.clip((f2 - f1) / 40.0, 0, 1)
    plateau = np.clip((edge - 0.12) * 3.0, 0, 1) ** 0.7
    yy = np.mgrid[0:HALF[0], 0:HALF[1]][0].astype(np.float32)
    layers = 0.5 + 0.5 * np.sin(yy / HALF[0] * 2 * np.pi * 60 + tex.fbm(HALF, 30, rng, 3) * 3)
    hgt = plateau * 10 + layers * 0.8 * plateau + 0.6 * tex.fbm(HALF, 8, rng, 3)
    pal = np.array([tex.srgb(c) for c in [(102, 90, 82), (118, 104, 94), (90, 76, 68), (110, 92, 80)]])
    col = pal[(_cellrand(cid, rng) * len(pal)).astype(int) % len(pal)]
    col = col * (0.82 + 0.3 * tex.norm01(tex.fbm(HALF, 25, rng, 4)))[..., None] * (0.9 + 0.1 * layers)[..., None]
    fissure = tex.srgb((84, 52, 40))
    deep = tex.srgb((40, 26, 20))
    col = _mix(_mix(deep, fissure, np.clip(edge * 6, 0, 1)), col, plateau)
    rough = 0.9 - 0.05 * plateau
    return col, hgt, rough


def pine_upper(rng):
    f1, f2, cid = _plates(rng, (10, 64), 6, 50, 0.9)
    edge = np.clip((f2 - f1) / 6.0, 0, 1)
    r = _cellrand(cid, rng)
    base = tex.srgb((192, 108, 60))
    pale = tex.srgb((214, 156, 112))
    dark = tex.srgb((150, 78, 44))
    col = _mix(base, pale, np.clip((r - 0.7) * 3, 0, 1) * 0.55)
    col = _mix(col, dark, np.clip((0.2 - r) * 5, 0, 1) * 0.45)
    n = tex.norm01(tex.fbm(HALF, 40, rng, 4))
    col = col * (0.88 + 0.2 * n)[..., None]
    col = _mix(tex.srgb((140, 76, 44)), col, np.clip(edge * 3.5, 0, 1))
    curl = np.clip(1 - edge, 0, 1) ** 4 * (r > 0.6)
    col = _mix(col, tex.srgb((228, 190, 150)), curl * 0.6)
    hgt = r * 1.2 + edge * 0.8 + curl * 1.0 + 0.2 * tex.fbm(HALF, 4, rng, 2)
    return col, hgt, 0.72 + 0.1 * (1 - edge)


# ----------------------------------------------------------------------------- birch
def birch_upper(rng):
    white = tex.srgb((222, 220, 210))
    n1 = tex.norm01(tex.fbm(HALF, 60, rng, 5))
    col = white * (0.88 + 0.14 * n1)[..., None]
    col = _mix(col, tex.srgb((196, 186, 176)), np.clip((tex.norm01(tex.fbm(HALF, 40, rng, 4, stretch=(4, 1))) - 0.6) * 2, 0, 0.6))
    # horizontal lenticels
    len_n = tex.fbm(HALF, 9, rng, 2, stretch=(9, 0.5))
    lent = np.clip((tex.norm01(len_n) - 0.8) * 8, 0, 1)
    col = _mix(col, tex.srgb((46, 40, 36)), lent * 0.95)
    # peeling papery bands (pinkish-tan)
    peel = np.clip((tex.norm01(tex.fbm(HALF, 30, rng, 3, stretch=(10, 1))) - 0.82) * 6, 0, 1)
    col = _mix(col, tex.srgb((206, 170, 146)), peel * 0.7)
    # dark patches / branch-scar 'eyes'
    blot = np.clip((tex.norm01(tex.fbm(HALF, 70, rng, 4, stretch=(2.5, 1))) - 0.9) * 8, 0, 1)
    col = _mix(col, tex.srgb((58, 54, 50)), blot)
    grime = tex.norm01(tex.fbm(HALF, 200, rng, 3))
    col = col * (0.9 + 0.1 * grime)[..., None]
    hgt = -lent * 1.5 + peel * 1.0 + blot * 0.8 + 0.25 * tex.fbm(HALF, 5, rng, 2)
    rough = 0.62 + 0.25 * lent + 0.2 * blot
    return col, hgt, rough


def birch_lower(rng):
    f1, f2, cid = _plates(rng, (8, 6), 18, 100, aniso=0.5)
    edge = np.clip((f2 - f1) / 22.0, 0, 1)
    plateau = np.clip(edge * 2.0, 0, 1) ** 0.8
    hgt = plateau * 9 + 0.7 * tex.fbm(HALF, 7, rng, 3)
    col = np.broadcast_to(tex.srgb((66, 62, 58)), HALF + (3,)).copy()
    col = col * (0.8 + 0.35 * tex.norm01(tex.fbm(HALF, 25, rng, 4)))[..., None]
    remnant = np.clip((tex.norm01(tex.fbm(HALF, 40, rng, 4, stretch=(3, 1))) - 0.62) * 5, 0, 1) * plateau
    col = _mix(col, tex.srgb((206, 202, 192)), remnant * 0.9)
    col = _mix(tex.srgb((24, 22, 20)), col, plateau)
    rough = 0.9 - 0.2 * remnant
    return col, hgt, rough


SPECIES = {
    "spruce": (spruce_lower, spruce_upper, 1.6),
    "pine": (pine_lower, pine_upper, 1.4),
    "birch": (birch_lower, birch_upper, 1.2),
}


def build_atlas(species, out_dir, out_dir_mobile, seed=7):
    rng = np.random.default_rng(seed)
    lo, up, nstr = SPECIES[species]
    cl, hl, rl = lo(rng)
    cu, hu, ru = up(rng)
    col = np.concatenate([cl, cu], axis=1)
    nrm = np.concatenate([tex.normal_from_height(hl, nstr), tex.normal_from_height(hu, nstr)], axis=1)
    rough = np.concatenate([np.broadcast_to(rl, HALF), np.broadcast_to(ru, HALF)], axis=1)
    files = {}
    for key, img in (("albedo", col), ("normal", nrm), ("rough", rough)):
        name = f"{species}_bark_{key}.png"
        tex.save_png(f"{out_dir}/{name}", img)
        tex.save_png(f"{out_dir_mobile}/{name}", tex.downsample2(img))
        files[key] = name
    tex.save_png(f"{out_dir}/{species}_bark_metalness.png", np.zeros((64, 64)))
    files["metalness"] = f"{species}_bark_metalness.png"
    return files
