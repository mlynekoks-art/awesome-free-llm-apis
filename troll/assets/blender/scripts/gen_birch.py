"""Downy birch (Betula pubescens): lowland form 12-15 m and crooked mountain birch
(B. pubescens ssp. czerepanovii / 'fjellbjørk') 3-5 m.

Traits modelled: white bark with dark horizontal lenticels, black fissured base (higher
on the lowland tree, a thin band on mountain birch); lowland form - single slightly
sinuous stem, narrow ovate crown of ascending branches whose outer twigs hang; mountain
form - multi-stemmed clump of crooked, leaning stems with a broad irregular crown and
small leaves (atlas variant B).

Run:  blender -b -P gen_birch.py -- [--only birch_lowland] [--no-render]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np  # noqa: E402
from norlib import geo, trees  # noqa: E402
from norlib.trees import Card, Tree, Tube  # noqa: E402
from gen_pine import crooked_path  # noqa: E402

VARIANTS = [
    dict(asset="birch_lowland", label="Birch_Lowland", seed=505, lod_render=True,
         params=dict(height=13.5, dbh=0.27, stems=1, crown_base=0.35, width_ratio=0.21, crooked=0.05,
                     lean=0.06, dark_base=1.3, leaf_variant=0, n_branches=26, branch_elev=(55, 30))),
    dict(asset="birch_mountain", label="Birch_Mountain", seed=606, lod_render=True,
         params=dict(height=4.3, dbh=0.11, stems=4, crown_base=0.25, width_ratio=0.42, crooked=0.22,
                     lean=0.45, dark_base=0.35, leaf_variant=1, n_branches=8, branch_elev=(40, 5))),
]
UP = np.array([0, 0, 1.0])


def generate(rng, height, dbh, stems, crown_base, width_ratio, crooked, lean, dark_base, leaf_variant,
             n_branches, branch_elev):
    t = Tree()
    Rmax = width_ratio * height
    top_z = 0.0
    az0 = rng.uniform(0, 6.28)
    for si in range(stems):
        if stems == 1:
            base = np.zeros(3)
            az = rng.uniform(0, 6.28)
            tilt = lean
            Ls = height
            r0 = dbh / 2
        else:
            az = az0 + 2 * math.pi * si / stems + rng.normal(0, 0.4)
            base = np.array([math.cos(az), math.sin(az), 0]) * rng.uniform(0.05, 0.18)
            tilt = lean * rng.uniform(0.5, 1.3)
            Ls = height * rng.uniform(0.75, 1.05) / math.cos(min(tilt, 1.0) * 0.8)
            r0 = dbh / 2 * rng.uniform(0.7, 1.1)
        d = geo.unit(np.array([math.cos(az) * math.sin(tilt), math.sin(az) * math.sin(tilt), math.cos(tilt)]))
        nseg = 14 if stems == 1 else 9
        path = crooked_path(rng, base, d, Ls, nseg, crooked, photo=0.04 if stems == 1 else 0.1)
        if stems > 1:   # basal sweep: mountain birch stems bend up from a sprawling base
            path[:, 2] = np.maximum(path[:, 2], 0)
        zs = path[:, 2]
        top_z = max(top_z, zs.max())
        sl = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))])
        frac = sl / sl[-1]
        rr = r0 * (1 - frac) ** 0.8 + 0.012
        rr *= 1 + 0.3 * np.exp(-zs / 0.3)
        # split bark: dark fissured base / white upper
        k = max(1, int(np.searchsorted(zs, dark_base)))
        k = min(k, len(path) - 2)
        t.tubes.append(Tube(path[:k + 1], rr[:k + 1], 0, (0.0, 0.5), cap=False))
        t.tubes.append(Tube(path[k:], rr[k:], 0, (0.5, 1.0)))
        _branches(t, rng, path, rr, sl, crown_base, Rmax, n_branches, branch_elev, crooked, leaf_variant, stems)
    t.info = dict(height=round(float(top_z), 2), stems=stems, dbh=dbh, crown_radius_max=round(Rmax, 2),
                  cards=len(t.cards), tubes=len(t.tubes), bark_frac={0: 0.25, 1: 0.25, 2: 0.15})
    return t


def _branches(t, rng, path, rr, sl, crown_base, Rmax, n, elev_rng, crooked, var, stems):
    total = sl[-1]
    golden = math.radians(137.5)
    az = rng.uniform(0, 6.28)
    axis_xy = (0.0, 0.0)
    card_sc = (0.8, 1.05) if var == 0 else (0.6, 0.85)
    for i in range(n):
        s = total * (crown_base + (1 - crown_base) * (i + rng.uniform(0, 0.9)) / n)
        rel = (s / total - crown_base) / (1 - crown_base)
        p = np.array([np.interp(s, sl, path[:, k]) for k in range(3)])
        r_here = float(np.interp(s, sl, rr))
        az += golden + rng.normal(0, 0.3)
        out = np.array([math.cos(az), math.sin(az), 0])
        shape = math.sin(math.pi * (0.15 + 0.75 * rel)) ** 0.7
        L = Rmax * shape * rng.uniform(0.7, 1.1) * (0.75 if stems > 1 else 1.0)
        L = max(L, 0.4 if var == 0 else 0.25)
        elev = math.radians(np.interp(rel, [0, 1], [elev_rng[1], elev_rng[0]]) + rng.normal(0, 7))
        d = geo.unit(out * math.cos(elev) + UP * math.sin(elev))
        bp = crooked_path(rng, p + out * r_here * 0.6, d, L, 5, 0.15 + crooked * 0.6, gravi=0.12)
        brr = np.linspace(min(0.012 + 0.018 * L, r_here * 0.6), 0.006, len(bp))
        t.tubes.append(Tube(bp, brr, 1 if L > 1.5 else 2, (0.5, 1.0)))
        limbs = [bp]
        for _ in range(int(rng.integers(2, 5))):
            j = int(rng.integers(1, len(bp) - 1))
            az2 = az + rng.choice([-1, 1]) * rng.uniform(0.4, 1.0)
            d2 = geo.unit(np.array([math.cos(az2), math.sin(az2), rng.uniform(-0.1, 0.6)]))
            rem = L * (1 - j / (len(bp) - 1))
            p2 = crooked_path(rng, bp[j], d2, max(rem * rng.uniform(0.4, 0.8), 0.3), 3, 0.25 + crooked, gravi=0.2)
            t.tubes.append(Tube(p2, np.linspace(brr[j] * 0.6, 0.004, len(p2)), 3, (0.5, 1.0)))
            limbs.append(p2)
        for lp in limbs:
            _leaf_cards(t, rng, lp, axis_xy, var, card_sc)
    # crown top: leafy cards around the stem tip
    tip = path[-1]
    for k in range(4):
        a = rng.uniform(0, 6.28)
        dd = geo.unit(np.array([math.cos(a) * 0.5, math.sin(a) * 0.5, 1.0]))
        nrm = geo.unit(np.cross(dd, np.array([-math.sin(a), math.cos(a), 0])))
        sc = rng.uniform(*card_sc)
        t.cards.append(Card(tip - dd * 0.4 * sc, dd, nrm, 1.0 * sc, 0.5 * sc, var, 0.1, 99.0,
                            trees.outward_dir(tip, axis_xy, 1.0)))


def _leaf_cards(t, rng, lp, axis_xy, var, card_sc):
    seg = np.linalg.norm(np.diff(lp, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    total = cum[-1]
    pos = total * rng.uniform(0.2, 0.35)
    step = 0.2 if var == 0 else 0.14
    while pos < total:
        p = np.array([np.interp(pos, cum, lp[:, k]) for k in range(3)])
        i = min(np.searchsorted(cum, pos), len(lp) - 1)
        T = geo.unit(lp[i] - lp[max(i - 1, 0)])
        hor = geo.unit(np.array([T[0], T[1], 0]) + 1e-9)
        side = geo.unit(np.cross(UP, hor))
        sc = rng.uniform(*card_sc)
        out = trees.outward_dir(p, axis_xy, 0.7)
        imp = sc * (0.5 + pos / total) * rng.uniform(0.6, 1.4)
        # hanging leafy twig (birch outer twigs droop)
        dh = geo.unit(hor * rng.uniform(0.3, 0.8) - UP * rng.uniform(0.4, 0.9) + side * rng.normal(0, 0.4))
        nh = geo.unit(np.cross(dh, side + hor * rng.normal(0, 0.3)))
        t.cards.append(Card(p, dh, nh, 1.0 * sc, 0.5 * sc, var, math.radians(rng.uniform(-10, 10)), imp, out))
        # spreading twig, roughly horizontal
        if rng.random() < 0.7:
            sd = rng.choice([-1, 1])
            ds = geo.unit(hor * 0.7 + side * sd * 0.7 + UP * rng.uniform(-0.1, 0.4))
            ns = geo.rotate(UP, ds, rng.normal(0, 0.5))
            t.cards.append(Card(p, ds, ns, 0.9 * sc, 0.5 * sc, var, math.radians(rng.uniform(5, 25)), imp * 0.8, out))
        pos += step * rng.uniform(0.8, 1.2) * sc


if __name__ == "__main__":
    trees.run_species("birch", VARIANTS, generate)
