"""Norway spruce (Picea abies) - mature, 22-28 m.

Traits modelled: straight monopodial trunk with slight root flare; regular annual whorls
(4-6 branches) plus small inter-whorl branches; narrow conical crown (width ~0.25-0.3 x
height); upper branches ascending, lower branches sweeping down with up-turned tips;
'comb' habit - secondary shoots hanging as curtains below the main branches in the
mid/lower crown; open-grown variant keeps live crown almost to the ground.

Run:  blender -b -P gen_spruce.py -- [--only spruce_a] [--no-render] [--samples 64]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from norlib import geo, trees  # noqa: E402
from norlib.trees import Card, Tree, Tube  # noqa: E402

VARIANTS = [
    dict(asset="spruce_a", label="Spruce_A", seed=11, lod_render=True,
         params=dict(height=26.0, dbh=0.52, crown_base=0.6, width_ratio=0.135, lean=0.02)),   # open-grown
    dict(asset="spruce_b", label="Spruce_B", seed=23,
         params=dict(height=23.0, dbh=0.42, crown_base=4.5, width_ratio=0.115, lean=0.05)),   # forest edge
    dict(asset="spruce_c", label="Spruce_C", seed=37,
         params=dict(height=28.0, dbh=0.58, crown_base=2.0, width_ratio=0.12, lean=0.03, sparse=0.25)),
]


def generate(rng, height, dbh, crown_base, width_ratio, lean, sparse=0.0):
    H = height
    t = Tree()
    # ------------------------------------------------------------------ trunk
    z = np.concatenate([np.arange(0, 3, 0.3), np.arange(3, H - 1.5, 0.9), np.linspace(H - 1.5, H, 4)])
    lean_dir = rng.uniform(0, 2 * math.pi)
    ph = rng.uniform(0, 6.28, 4)
    off_x = lean * z * math.cos(lean_dir) + 0.06 * np.sin(z / 3.1 + ph[0]) + 0.03 * np.sin(z / 1.3 + ph[1])
    off_y = lean * z * math.sin(lean_dir) + 0.06 * np.sin(z / 2.7 + ph[2]) + 0.03 * np.sin(z / 1.1 + ph[3])
    off_x -= off_x[0]
    off_y -= off_y[0]
    pts = np.stack([off_x, off_y, z], 1)
    r = (dbh / 2) * np.clip((H - z) / (H - 1.3), 0, None) ** 0.85
    r *= 1 + 0.45 * np.exp(-z / 0.5)
    r = np.maximum(r, 0.006)
    lobes = rng.integers(4, 7)
    lob_ph = rng.uniform(0, 6.28)
    flare = lambda i, a: 1 + 0.35 * math.exp(-z[i] / 0.35) * max(0.0, math.cos(lobes * a + lob_ph)) ** 2
    split = int(np.searchsorted(z, H * 0.45))
    t.tubes.append(Tube(pts[:split + 1], r[:split + 1], 0, (0.0, 0.5), flare=flare, cap=False))
    t.tubes.append(Tube(pts[split:], r[split:], 0, (0.5, 1.0)))

    def axis_at(zz):
        return np.array([np.interp(zz, z, off_x), np.interp(zz, z, off_y), zz])

    def r_at(zz):
        return float(np.interp(zz, z, r))

    # ------------------------------------------------------------------ branches
    Lc = H - crown_base
    Rmax = width_ratio * H
    zz = crown_base
    whorl = 0
    up = np.array([0, 0, 1.0])
    golden = math.radians(137.5)
    az0 = rng.uniform(0, 6.28)
    while zz < H - 0.35:
        d_top = H - zz
        rel = d_top / Lc                        # 0 at top .. 1 at crown base
        nb = int(rng.integers(4, 7)) if rel > 0.05 else 3
        extra = int(rng.integers(0, 3)) if rel > 0.15 else 0
        for k in range(nb + extra):
            inter = k >= nb
            bz = zz + (rng.uniform(0.1, 0.35) if inter else rng.uniform(-0.03, 0.03))
            if bz > H - 0.3:
                continue
            az = az0 + whorl * golden + 2 * math.pi * k / max(nb, 1) + rng.normal(0, 0.25)
            prof = rel ** 0.78 if rel < 1 else 1.0
            L = Rmax * prof * rng.uniform(0.78, 1.12)
            if rel > 0.85 and crown_base > 2.0:
                L *= 1 - 0.35 * (rel - 0.85) / 0.15        # suppressed lowest branches
            if inter:
                L *= rng.uniform(0.35, 0.6)
            L = max(L, 0.25 + 0.25 * rng.random())
            if sparse and rng.random() < sparse * rel:
                continue                                   # gaps in the crown (variant C)
            _branch(t, rng, axis_at(bz), r_at(bz), az, L, rel, inter, (axis_at(bz)[0], axis_at(bz)[1]))
        zz += rng.uniform(0.32, 0.55) * (0.8 + 0.3 * min(rel * 2, 1))
        whorl += 1
    # leader spire
    top = axis_at(H - 1.4)
    for k in range(2):
        a = k * math.pi / 2 + rng.uniform(0, 0.3)
        nrm = np.array([math.cos(a), math.sin(a), 0])
        t.cards.append(Card(top, up, nrm, 1.5, 0.45, 0, 0.0, 99.0, outward=up))
    # dead stubs under the live crown (forest-grown)
    if crown_base > 2.0:
        for _ in range(int(crown_base * 3)):
            bz = rng.uniform(1.0, crown_base)
            a = rng.uniform(0, 6.28)
            d = np.array([math.cos(a), math.sin(a), rng.uniform(-0.4, 0.0)])
            p0 = axis_at(bz)
            L = rng.uniform(0.15, 0.6)
            t.tubes.append(Tube(np.array([p0, p0 + geo.unit(d) * L]), np.array([0.02, 0.008]), 2, (0.5, 1.0)))
    t.info = dict(height=H, dbh=dbh, crown_base=crown_base, crown_radius_max=round(Rmax, 2),
                  cards=len(t.cards), tubes=len(t.tubes))
    return t


def _branch(t, rng, origin, trunk_r, az, L, rel, inter, axis_xy):
    """One primary branch with its foliage cards."""
    hor = np.array([math.cos(az), math.sin(az), 0.0])
    theta0 = math.radians(np.interp(rel, [0, 0.3, 1], [45, 12, -12]) + rng.normal(0, 6))
    droop = math.radians(np.interp(rel, [0, 0.3, 1], [5, 25, 50]) * rng.uniform(0.8, 1.2))
    upturn = math.radians(np.interp(rel, [0, 0.3, 1], [0, 25, 55]) * rng.uniform(0.7, 1.2))
    nseg = 6
    pts = [origin + hor * trunk_r * 0.8]
    yaw = rng.normal(0, 0.08)
    for i in range(nseg):
        s = (i + 0.5) / nseg
        th = theta0 - droop * min(s / 0.7, 1) + upturn * max(0, (s - 0.65) / 0.35) ** 1.5
        h = geo.rotate(hor, np.array([0, 0, 1.0]), yaw * i)
        d = h * math.cos(th) + np.array([0, 0, 1.0]) * math.sin(th)
        pts.append(pts[-1] + d * L / nseg)
    pts = np.array(pts)
    rb = min(0.008 + 0.02 * L, trunk_r * 0.6)
    radii = np.linspace(rb, 0.006, len(pts))
    level = 1 if L > 1.4 else 2
    if L > 0.9:
        t.tubes.append(Tube(pts, radii, level, (0.0, 0.5)))
    # ---- foliage cards
    seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seglen)])
    total = cum[-1]
    s_card = float(np.clip(0.6 + 0.3 * L, 0.6, 1.5)) * (0.75 if inter else 1.0)
    start = total * (0.3 if rel > 0.4 else 0.1)
    pos = start
    upv = np.array([0, 0, 1.0])
    while pos < total - 0.15 * s_card:
        p = np.array([np.interp(pos, cum, pts[:, k]) for k in range(3)])
        i = min(np.searchsorted(cum, pos), len(pts) - 1)
        T = geo.unit(pts[i] - pts[max(i - 1, 0)])
        side = geo.unit(np.cross(upv, T))
        out = trees.outward_dir(p, axis_xy, 0.5)
        tipness = pos / total
        imp = (0.6 + tipness) * s_card * (1.5 - 0.5 * rel) * rng.uniform(0.6, 1.4)
        # flat spray following the branch
        d = geo.unit(T + side * rng.normal(0, 0.25) + upv * rng.uniform(-0.05, 0.1))
        roll = rng.normal(0, 0.35)
        nrm = geo.rotate(upv, d, roll)
        t.cards.append(Card(p, d, nrm, 1.0 * s_card, 0.5 * s_card, 0,
                            math.radians(rng.uniform(10, 30)), imp, out))
        # side-angled spray for volume
        if rng.random() < 0.6:
            sd = 1 if rng.random() < 0.5 else -1
            d2 = geo.unit(T * 0.8 + side * sd * 0.6 - upv * 0.1)
            n2 = geo.rotate(upv, d2, sd * rng.uniform(0.4, 0.8))
            t.cards.append(Card(p, d2, n2, 0.8 * s_card, 0.45 * s_card, 0,
                                math.radians(rng.uniform(15, 35)), imp * 0.8, out))
        # hanging 'comb' curtains in the mid/lower crown
        if rel > 0.22:
            for _ in range(int(rng.integers(1, 3))):
                off = side * rng.uniform(-0.15, 0.15) * s_card
                dh = geo.unit(-upv * 0.9 + T * rng.uniform(0.1, 0.4) + side * rng.normal(0, 0.15))
                nh = geo.unit(np.cross(dh, T)) * (1 if rng.random() < 0.5 else -1)
                t.cards.append(Card(p + off, dh, nh, rng.uniform(0.55, 0.9) * s_card, 0.42 * s_card, 1,
                                    math.radians(-rng.uniform(0, 12)), imp * 0.55, out))
        pos += 0.42 * s_card * rng.uniform(0.85, 1.15)
    return pts


if __name__ == "__main__":
    trees.run_species("spruce", VARIANTS, generate)
