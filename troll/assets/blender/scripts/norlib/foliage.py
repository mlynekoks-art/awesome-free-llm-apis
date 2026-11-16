"""Foliage card atlases: needle sprays (spruce, pine) and leafy twigs (birch).

Each atlas is 1024x1024: left half (u 0..0.5) = variant A, right half (u 0.5..1) = variant B.
A card half is 512x1024 px and represents a physical 0.5 m x 1.0 m branch spray, so the
painter works at 1024 px/m.  The spray base (where it attaches to the branch) is at v = 0,
the tip at v = 1.  Needles are generated in 3D around each shoot and orthographically
projected, so they bristle in all directions like real shoots.
"""
import numpy as np
from . import tex

CARD_W, CARD_H, PPM = 512, 1024, 1024.0


def _polyline(p0, direction, length, n, curl, rng, wobble=0.0):
    """3D polyline from p0 heading `direction` (3,), curling in the card plane."""
    pts = [np.array(p0, np.float32)]
    d = np.array(direction, np.float32)
    d /= np.linalg.norm(d)
    step = length / n
    for i in range(n):
        ang = curl / n + rng.normal(0, wobble)
        c, s = np.cos(ang), np.sin(ang)
        d = np.array([c * d[0] - s * d[1], s * d[0] + c * d[1], d[2]], np.float32)
        d /= np.linalg.norm(d)
        pts.append(pts[-1] + d * step)
    return np.array(pts)


def _resample(poly, spacing, rng, jitter=0.3):
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1)
    cum = np.concatenate([[0], np.cumsum(seg)])
    total = cum[-1]
    s = np.arange(spacing * rng.random(), total, spacing)
    s = np.clip(s + rng.uniform(-jitter, jitter, s.size) * spacing, 0, total)
    pos = np.stack([np.interp(s, cum, poly[:, k]) for k in range(3)], 1)
    i = np.clip(np.searchsorted(cum, s) - 1, 0, len(seg) - 1)
    tan = (poly[i + 1] - poly[i]) / np.maximum(seg[i], 1e-6)[:, None]
    return pos, tan, s / max(total, 1e-6), total


def _needles(cv, shoots, rng, length, radius, alpha_deg, spacing, colours, up_bias,
             tip_fresh=0.0, fresh_col=None, rough=0.55, curve=0.0, pairs=False):
    """shoots: list of 3D polylines.  Draw needles around them."""
    P0, P1, Z0, Z1, C = [], [], [], [], []
    for poly in shoots:
        pos, tan, frac, total = _resample(poly, spacing, rng)
        if len(pos) == 0:
            continue
        n = len(pos)
        side = np.stack([-tan[:, 1], tan[:, 0], np.zeros(n)], 1)
        side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-6)
        zax = np.cross(tan, side)
        reps = 2 if pairs else 1
        for r in range(reps):
            phi = rng.uniform(0, 2 * np.pi, n)
            flip = (np.sin(phi) < -0.2) & (rng.random(n) < up_bias)
            phi = np.where(flip, -phi, phi)
            a = np.radians(alpha_deg + rng.normal(0, 9, n))
            radial = np.cos(phi)[:, None] * side + np.sin(phi)[:, None] * zax
            d = np.cos(a)[:, None] * tan + np.sin(a)[:, None] * radial
            L = length * rng.uniform(0.75, 1.2, n) * (0.55 + 0.45 * np.clip((1 - frac) * 6, 0, 1) ** 0.3)
            tip = pos + d * L[:, None]
            col = colours[rng.integers(0, len(colours), n)] * rng.uniform(0.85, 1.12, (n, 1))
            if tip_fresh and fresh_col is not None:
                dist_tip = (1 - frac) * total
                fm = np.clip(1 - dist_tip / tip_fresh, 0, 1)[:, None] * 0.8
                col = col * (1 - fm) + fresh_col * fm
            if curve:
                mid = pos + d * (L * 0.5)[:, None] + radial * (L * curve)[:, None]
                P0 += [pos[:, :2], mid[:, :2]]; P1 += [mid[:, :2], tip[:, :2]]
                Z0 += [pos[:, 2], mid[:, 2]]; Z1 += [mid[:, 2], tip[:, 2]]; C += [col, col]
            else:
                P0.append(pos[:, :2]); P1.append(tip[:, :2]); Z0.append(pos[:, 2]); Z1.append(tip[:, 2]); C.append(col)
    P0, P1 = np.concatenate(P0), np.concatenate(P1)
    Z0, Z1, C = np.concatenate(Z0), np.concatenate(Z1), np.concatenate(C)
    cv.capsules(P0, P1, radius, radius * 0.45, Z0, Z1, np.clip(C, 0, 1), rough)


def _twigs(cv, shoots, r0, r1, col, rough=0.85, z_off=0.0):
    for poly in shoots:
        n = len(poly) - 1
        rr = np.linspace(r0, r1, n + 1)
        cv.capsules(poly[:-1, :2], poly[1:, :2], rr[:-1], rr[1:], poly[:-1, 2] + z_off,
                    poly[1:, 2] + z_off, col, rough)


def _clip_reach(poly, max_x=0.225, max_y=0.975):
    keep = (np.abs(poly[:, 0]) < max_x) & (poly[:, 1] < max_y) & (poly[:, 1] > -0.001)
    if keep.all():
        return poly
    first_bad = np.argmin(keep) if not keep.all() else len(poly)
    return poly[:max(first_bad, 2)]


# ============================================================================ spruce
def spruce_spray(rng, pendulous=False):
    cv = tex.Canvas(CARD_W, CARD_H, PPM)
    main = _polyline((rng.uniform(-0.01, 0.01), 0.0, 0.012), (rng.normal(0, 0.03), 1, 0), 0.95, 24,
                     rng.normal(0, 0.15), rng, 0.02)
    main = _clip_reach(main)
    shoots1, shoots2 = [], []
    s = 0.04
    side = 1
    while s < 0.9:
        i = int(s / 0.95 * (len(main) - 1))
        base = main[i]
        env = (1 - s / 0.95) ** 0.55 * min(1.0, 0.45 + s / 0.12)
        if pendulous:
            ang = np.radians(rng.uniform(22, 34)) * side
            ln = 0.52 * env * rng.uniform(0.8, 1.1)
        else:
            ang = np.radians(rng.uniform(48, 62)) * side
            ln = min(0.21 / np.sin(abs(ang)), 0.32) * env * rng.uniform(0.8, 1.1)
        if ln > 0.03:
            d0 = main[min(i + 1, len(main) - 1)] - main[max(i - 1, 0)]
            d0 /= np.linalg.norm(d0) + 1e-9
            c, sn = np.cos(ang), np.sin(ang)
            d = (c * d0[0] - sn * d0[1], sn * d0[0] + c * d0[1], -0.12)
            sh = _clip_reach(_polyline(base, d, ln, 10, -side * rng.uniform(0.1, 0.35), rng, 0.03))
            shoots1.append(sh)
            t = 0.05
            sd = -side
            while t < ln * 0.8:
                j = int(t / ln * (len(sh) - 1))
                rem = ln - t
                l2 = 0.6 * rem * rng.uniform(0.7, 1.1)
                if l2 > 0.025 and j < len(sh) - 1:
                    dd = sh[j + 1] - sh[j]
                    dd /= np.linalg.norm(dd) + 1e-9
                    a2 = np.radians(rng.uniform(40, 55)) * sd
                    c2, s2 = np.cos(a2), np.sin(a2)
                    d2 = (c2 * dd[0] - s2 * dd[1], s2 * dd[0] + c2 * dd[1], -0.15)
                    shoots2.append(_clip_reach(_polyline(sh[j], d2, l2, 5, 0, rng, 0.03)))
                t += rng.uniform(0.02, 0.032)
                sd = -sd
        s += rng.uniform(0.022, 0.034)
        side = -side
    twig = tex.srgb((112, 74, 44))
    _twigs(cv, [main], 0.0040, 0.0012, twig)
    _twigs(cv, shoots1, 0.0018, 0.0008, twig * 0.95)
    _twigs(cv, shoots2, 0.0011, 0.0006, twig * 0.9)
    greens = np.array([tex.srgb(c) for c in [(30, 52, 26), (36, 60, 30), (28, 48, 28), (42, 66, 34), (33, 55, 36)]])
    fresh = tex.srgb((70, 102, 44))
    _needles(cv, [main] + shoots1 + shoots2, rng, 0.019, 0.0007, 60, 0.0014, greens, 0.75,
             tip_fresh=0.05, fresh_col=fresh, rough=0.5)
    return cv.finish(normal_strength=0.9, ao=0.5)


# ============================================================================ pine
def pine_spray(rng, dense=False):
    cv = tex.Canvas(CARD_W, CARD_H, PPM)
    shoots, brushes = [], []
    if not dense:
        main = _polyline((0, 0.0, 0.0), (rng.normal(0, 0.05), 1, 0.05), 0.4, 10, rng.normal(0, 0.2), rng, 0.03)
        shoots.append(main)
        tip = main[-1]
        dirs = [(0.0, 1.0), (-0.45, 1.0), (0.45, 1.0)] + ([(rng.choice([-0.8, 0.8]), 1.0)] if rng.random() < 0.6 else [])
        for dx, dy in dirs:
            ln = rng.uniform(0.4, 0.52) if dx == 0 else rng.uniform(0.3, 0.42)
            sh = _clip_reach(_polyline(tip, (dx + rng.normal(0, 0.08), dy, 0.03), ln, 8, rng.normal(0, 0.15), rng, 0.04),
                             0.2, 0.94)
            shoots.append(sh)
            brushes.append(sh)
        # older needles along upper half of main shoot
        brushes.append(main[len(main) // 2:])
    else:
        base = np.array([0.0, 0.05, 0.0])
        for k in range(5):
            ang = np.radians(-34 + 17 * k + rng.normal(0, 5))
            ln = rng.uniform(0.6, 0.82) * (1 - 0.25 * abs(k - 2) / 2)
            sh = _clip_reach(_polyline(base, (np.sin(ang), np.cos(ang), 0.02), ln, 10, rng.normal(0, 0.1), rng, 0.03),
                             0.2, 0.94)
            shoots.append(sh)
            brushes.append(sh[int(len(sh) * 0.3):])
    _twigs(cv, shoots, 0.0075, 0.0035, tex.srgb((120, 84, 58)), z_off=-0.002)
    greens = np.array([tex.srgb(c) for c in [(66, 90, 74), (76, 98, 78), (58, 82, 68), (84, 104, 82), (70, 94, 84)]])
    _needles(cv, brushes, rng, 0.06, 0.0009, 40, 0.0018, greens, 0.4, rough=0.45, curve=0.08, pairs=True)
    # a few brownish older/dying needles inside the brush
    _needles(cv, [b[: max(2, len(b) // 3)] for b in brushes], rng, 0.042, 0.0008, 55, 0.02,
             np.array([tex.srgb((120, 98, 58)), tex.srgb((98, 90, 60))]), 0.2, rough=0.6, curve=0.05)
    return cv.finish(normal_strength=0.8, ao=0.5)


# ============================================================================ birch
def birch_spray(rng, small_leaves=False):
    cv = tex.Canvas(CARD_W, CARD_H, PPM)
    leaf_len = (0.018, 0.03) if small_leaves else (0.03, 0.05)
    twig_col = tex.srgb((78, 52, 40))
    main = _polyline((0, 0, 0), (rng.normal(0, 0.1), 1, 0), 0.92, 26, rng.normal(0, 0.3), rng, 0.06)
    main = _clip_reach(main)
    twigs = [main]
    s = 0.08
    side = 1
    while s < 0.85:
        i = int(s / 0.92 * (len(main) - 1))
        ln = rng.uniform(0.12, 0.32) * (1 - s * 0.6)
        ang = np.radians(rng.uniform(35, 60)) * side
        d0 = main[min(i + 1, len(main) - 1)] - main[i]
        d0 /= np.linalg.norm(d0) + 1e-9
        c, sn = np.cos(ang), np.sin(ang)
        d = (c * d0[0] - sn * d0[1], sn * d0[0] + c * d0[1], 0)
        twigs.append(_clip_reach(_polyline(main[i], d, ln, 8, -side * 0.3, rng, 0.08), 0.21, 0.95))
        s += rng.uniform(0.045, 0.08)
        side = -side
    _twigs(cv, twigs[:1], 0.003, 0.0012, twig_col)
    _twigs(cv, twigs[1:], 0.0016, 0.0008, twig_col * 1.1)
    up_cols = [tex.srgb(c) for c in [(78, 110, 42), (88, 120, 46), (70, 100, 40), (96, 124, 52), (82, 112, 50)]]
    under = tex.srgb((128, 146, 92))
    for tw in twigs:
        pos, tan, frac, total = _resample(tw[:, :], 0.022 if not small_leaves else 0.016, rng, 0.25)
        for k in range(len(pos)):
            if frac[k] < 0.08:
                continue
            sd = 1 if k % 2 else -1
            ang = np.radians(rng.uniform(30, 75)) * sd
            t = tan[k]
            c, sn = np.cos(ang), np.sin(ang)
            d = np.array([c * t[0] - sn * t[1], sn * t[0] + c * t[1]])
            d /= np.linalg.norm(d) + 1e-9
            pet = 0.012 * rng.uniform(0.7, 1.3)
            b = pos[k, :2] + d * pet
            z = rng.uniform(-0.01, 0.012)
            cv.capsules(pos[k, :2][None], b[None], 0.0005, 0.0004, z, z, twig_col * 1.3, 0.8)
            L = rng.uniform(*leaf_len)
            tilt = abs(np.cos(rng.uniform(0, 1.25)))
            underside = rng.random() < 0.18
            col = (under if underside else up_cols[rng.integers(len(up_cols))]) * rng.uniform(0.88, 1.1)
            col = col * (0.75 + 0.25 * tilt)
            leaf_dir = d + rng.normal(0, 0.25, 2)
            leaf_dir /= np.linalg.norm(leaf_dir)
            cv.polygon_leaf(b, leaf_dir, L, L * rng.uniform(0.62, 0.8), z, np.clip(col, 0, 1),
                            0.5 if not underside else 0.7, tilt=tilt, shape=0.45,
                            vein_col=np.clip(col * 1.12, 0, 1))
            if rng.random() < 0.35:   # short-shoot pair
                d2 = d + rng.normal(0, 0.5, 2)
                d2 /= np.linalg.norm(d2)
                cv.polygon_leaf(b, d2, L * 0.8, L * 0.55, z - 0.002, np.clip(col * 0.9, 0, 1), 0.55,
                                tilt=abs(np.cos(rng.uniform(0, 1.3))), shape=0.45)
    return cv.finish(normal_strength=1.0, ao=0.4)


# ============================================================================ atlas
BUILDERS = {
    "spruce": (lambda r: spruce_spray(r, False), lambda r: spruce_spray(r, True)),
    "pine": (lambda r: pine_spray(r, False), lambda r: pine_spray(r, True)),
    "birch": (lambda r: birch_spray(r, False), lambda r: birch_spray(r, True)),
}


def build_atlas(species, out_dir, out_dir_mobile, seed=1):
    rng = np.random.default_rng(seed)
    a, b = BUILDERS[species]
    ma, mb = a(rng), b(rng)
    files = {}
    for key in ("albedo", "normal", "rough", "alpha"):
        img = np.concatenate([ma[key], mb[key]], axis=1)
        name = f"{species}_foliage_{key}.png"
        tex.save_png(f"{out_dir}/{name}", img)
        tex.save_png(f"{out_dir_mobile}/{name}", tex.downsample2(img))
        files[key] = name
    tex.save_png(f"{out_dir}/{species}_foliage_metalness.png", np.zeros((64, 64)))
    files["metalness"] = f"{species}_foliage_metalness.png"
    return files
