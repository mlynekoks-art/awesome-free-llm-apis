"""Scots pine (Pinus sylvestris) - mature, 16-22 m.

Traits modelled: long clear bole (self-pruned, a few dead stubs) with thick grey-brown
fissured bark low down switching to thin orange-red flaky bark on the upper trunk and limbs;
live crown only in the top ~30-45 %; apical dominance lost in old trees -> leader forks into
several ascending limbs giving an irregular, flattened/umbrella crown; few, crooked,
sinuous limbs with foliage concentrated in dense blue-green pads at the limb ends.

Run:  blender -b -P gen_pine.py -- [--only pine_a] [--no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from norlib import geo, trees  # noqa: E402
from norlib.trees import Card, Tree, Tube  # noqa: E402

VARIANTS = [
    dict(asset="pine_a", label="Pine_A", seed=101, lod_render=True,
         params=dict(height=20.0, dbh=0.42, crown_frac=0.38, width_ratio=0.27, forks=3, lean=0.03)),
    dict(asset="pine_b", label="Pine_B", seed=202,
         params=dict(height=17.0, dbh=0.36, crown_frac=0.45, width_ratio=0.3, forks=2, lean=0.06)),
    dict(asset="pine_c", label="Pine_C", seed=303,
         params=dict(height=22.0, dbh=0.48, crown_frac=0.3, width_ratio=0.24, forks=4, lean=0.02)),
]

UP = np.array([0, 0, 1.0])


def crooked_path(rng, start, direction, length, nseg, wobble, gravi=0.0, photo=0.0):
    """Sinuous limb path: random kinks plus optional bending to horizontal (gravi) or up (photo)."""
    pts = [np.asarray(start, float)]
    d = geo.unit(direction)
    for i in range(nseg):
        axis = geo.perp(d)
        d = geo.rotate(d, axis, rng.normal(0, wobble))
        d = geo.rotate(d, d, 0)  # keep normalised
        hor = geo.unit(np.array([d[0], d[1], 0.0]) + 1e-9)
        if gravi:
            d = geo.unit(d * (1 - gravi) + hor * gravi)
        if photo:
            d = geo.unit(d + UP * photo)
        pts.append(pts[-1] + d * length / nseg)
    return np.array(pts)


def generate(rng, height, dbh, crown_frac, width_ratio, forks, lean):
    H = height
    t = Tree()
    cb = H * (1 - crown_frac)                       # live crown base
    fork_z = H * rng.uniform(0.8, 0.86)
    # ------------------------------------------------------------------ bole
    z = np.concatenate([np.arange(0, 2.5, 0.35), np.arange(2.5, fork_z, 0.8), [fork_z]])
    lean_dir = rng.uniform(0, 6.28)
    ph = rng.uniform(0, 6.28, 4)
    ox = lean * z * math.cos(lean_dir) + 0.12 * np.sin(z / 4.0 + ph[0]) * (z / H) + 0.04 * np.sin(z / 1.7 + ph[1])
    oy = lean * z * math.sin(lean_dir) + 0.12 * np.sin(z / 3.3 + ph[2]) * (z / H) + 0.04 * np.sin(z / 1.5 + ph[3])
    ox -= ox[0]
    oy -= oy[0]
    pts = np.stack([ox, oy, z], 1)
    r = (dbh / 2) * np.clip((H - z) / (H - 1.3), 0, None) ** 0.75
    r *= 1 + 0.35 * np.exp(-z / 0.45)
    r = np.maximum(r, 0.03)
    lobes = rng.integers(3, 6)
    lph = rng.uniform(0, 6.28)
    flare = lambda i, a: 1 + 0.3 * math.exp(-z[i] / 0.3) * max(0.0, math.cos(lobes * a + lph)) ** 2
    bark_split = H * rng.uniform(0.38, 0.5)          # thick grey bark -> orange 'mirror' bark
    k = int(np.searchsorted(z, bark_split))
    v_end = 0.0
    t.tubes.append(Tube(pts[:k + 1], r[:k + 1], 0, (0.0, 0.5), flare=flare, cap=False))
    t.tubes.append(Tube(pts[k:], r[k:], 0, (0.5, 1.0), cap=False))
    axis_xy = (ox[-1], oy[-1])

    def axis_at(zz):
        return np.array([np.interp(zz, z, ox), np.interp(zz, z, oy), zz])

    def r_at(zz):
        return float(np.interp(zz, z, r))

    Rmax = width_ratio * H
    tips = []                                          # (path, level) that carry foliage
    # ------------------------------------------------------------------ leader forks
    top = pts[-1]
    for f in range(forks):
        az = rng.uniform(0, 6.28) if f == 0 else az0 + 2 * math.pi * f / forks + rng.normal(0, 0.3)
        if f == 0:
            az0 = az
        out = np.array([math.cos(az), math.sin(az), 0])
        d = geo.unit(UP * rng.uniform(1.2, 2.5) + out)
        L = (H - fork_z) * rng.uniform(1.1, 1.5)
        path = crooked_path(rng, top, d, L, 6, 0.2, gravi=0.12)
        rr = np.linspace(r[-1] * rng.uniform(0.6, 0.8), 0.025, len(path))
        t.tubes.append(Tube(path, rr, 1, (0.5, 1.0)))
        tips.append((path, 1))
        for s in range(int(rng.integers(1, 3))):         # side branches of the forks
            j = int(rng.integers(2, len(path) - 1))
            az2 = az + rng.choice([-1, 1]) * rng.uniform(0.6, 1.3)
            d2 = geo.unit(np.array([math.cos(az2), math.sin(az2), rng.uniform(0.1, 0.6)]))
            p2 = crooked_path(rng, path[j], d2, Rmax * rng.uniform(0.35, 0.6), 4, 0.25, gravi=0.15)
            t.tubes.append(Tube(p2, np.linspace(rr[j] * 0.6, 0.015, len(p2)), 2, (0.5, 1.0)))
            tips.append((p2, 2))
    # ------------------------------------------------------------------ main limbs
    n_limbs = int(rng.integers(11, 17))
    golden = math.radians(137.5)
    az_base = rng.uniform(0, 6.28)
    for i in range(n_limbs):
        zz = cb + (fork_z - cb) * (i + rng.uniform(0.0, 0.8)) / n_limbs
        rel = (zz - cb) / max(H - cb, 1e-3)                 # 0 crown base .. 1 top
        az = az_base + i * golden + rng.normal(0, 0.3)
        out = np.array([math.cos(az), math.sin(az), 0])
        prof = 0.45 + 0.6 * math.sin(math.pi * (0.5 + (rel - 0.7) * 0.7))   # widest high up: flat-topped crown
        L = Rmax * prof * rng.uniform(0.75, 1.15)
        elev = math.radians(np.interp(rel, [0, 1], [2, 35]) + rng.normal(0, 8))
        d = geo.unit(out * math.cos(elev) + UP * math.sin(elev))
        start = axis_at(zz) + out * r_at(zz) * 0.7
        path = crooked_path(rng, start, d, L, 7, 0.3, gravi=0.1, photo=0.05)
        rb = min(0.045 + 0.035 * L, r_at(zz) * 0.6)
        rr = np.linspace(rb, 0.012, len(path))
        t.tubes.append(Tube(path, rr, 1, (0.5, 1.0)))
        dead = rel < 0.12 and rng.random() < 0.5
        if not dead:
            tips.append((path, 1))
        # sub-limbs on the outer part
        for s in range(int(rng.integers(3, 6))):
            j = int(rng.integers(len(path) // 4, len(path) - 1))
            az2 = az + rng.choice([-1, 1]) * rng.uniform(0.4, 1.1)
            d2 = geo.unit(np.array([math.cos(az2), math.sin(az2), rng.uniform(0.05, 0.5)]))
            rem = L * (1 - j / (len(path) - 1))
            p2 = crooked_path(rng, path[j], d2, max(rem * rng.uniform(0.5, 0.9), 0.5), 4, 0.3, gravi=0.15, photo=0.05)
            t.tubes.append(Tube(p2, np.linspace(rr[j] * 0.65, 0.01, len(p2)), 2, (0.5, 1.0)))
            if not dead:
                tips.append((p2, 2))
    # ------------------------------------------------------------------ dead stubs on the bole
    for _ in range(int(rng.integers(6, 14))):
        zz = rng.uniform(2.0, cb)
        a = rng.uniform(0, 6.28)
        d = geo.unit(np.array([math.cos(a), math.sin(a), rng.uniform(-0.3, 0.3)]))
        p0 = axis_at(zz) + d * r_at(zz) * 0.5
        L = rng.uniform(0.08, 0.35)
        t.tubes.append(Tube(np.array([p0, p0 + d * L]), np.array([0.025, 0.012]), 3, (0.0, 0.5)))
    # ------------------------------------------------------------------ foliage pads
    for path, lvl in tips:
        seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
        cum = np.concatenate([[0], np.cumsum(seg)])
        total = cum[-1]
        span = min(total * 0.7, 2.4)
        n = int(np.clip(span / 0.075, 8, 30))
        for c in range(n):
            s = total - span * rng.random() ** 0.7
            p = np.array([np.interp(s, cum, path[:, k]) for k in range(3)])
            i = min(np.searchsorted(cum, s), len(path) - 1)
            T = geo.unit(path[i] - path[max(i - 1, 0)])
            hor = geo.unit(np.array([T[0], T[1], 0]) + 1e-9)
            side = geo.unit(np.cross(UP, hor))
            spread = rng.normal(0, 0.7)
            d = geo.unit(hor * math.cos(spread) + side * math.sin(spread) + UP * rng.uniform(0.0, 0.55))
            nrm = geo.rotate(UP, d, rng.normal(0, 0.45))
            sc = rng.uniform(0.85, 1.25)
            outv = trees.outward_dir(p, axis_xy, 0.9)
            imp = sc * (1.2 if s > total - span * 0.4 else 0.8) * rng.uniform(0.7, 1.3)
            var = 0 if rng.random() < 0.65 else 1
            t.cards.append(Card(p - d * 0.15, d, nrm, 0.95 * sc, 0.55 * sc, var,
                                math.radians(rng.uniform(5, 25)), imp, outv))
        # crown-top tufts: an up-pointing card pair at each tip
        tip = path[-1]
        Tt = geo.unit(path[-1] - path[-2])
        for k in range(2):
            a = rng.uniform(0, 3.14)
            nrm = np.array([math.cos(a), math.sin(a), 0])
            dd = geo.unit(Tt * 0.5 + UP * 0.8)
            t.cards.append(Card(tip - dd * 0.35, dd, nrm, 0.8, 0.5, 1, 0.1, 1.5,
                                trees.outward_dir(tip, axis_xy, 0.9)))
    t.info = dict(height=H, dbh=dbh, crown_base=round(cb, 2), fork_height=round(fork_z, 2),
                  bark_transition=round(bark_split, 2), crown_radius_max=round(Rmax, 2),
                  cards=len(t.cards), tubes=len(t.tubes), bark_frac={0: 0.36, 1: 0.32, 2: 0.25})
    return t


if __name__ == "__main__":
    trees.run_species("pine", VARIANTS, generate)
