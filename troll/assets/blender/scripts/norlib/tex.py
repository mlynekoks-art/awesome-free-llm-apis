"""Numpy texture synthesis.  Works in Blender's bundled Python and in plain CPython+numpy.

Conventions
-----------
* Arrays are (H, W[, C]) float32 in 0..1 with ROW 0 = BOTTOM of the image (v = 0),
  so array rows map directly to UV v.  `save_png` flips to PNG's top-first order.
* Colours given as sRGB 0..255 tuples are stored as sRGB-encoded values (albedo PNGs
  are sRGB, normal/roughness/alpha PNGs are linear data).
* Normal maps are tangent space, OpenGL convention (+Y = +v), as used by Blender and
  Roblox SurfaceAppearance.
"""
import struct
import zlib
import numpy as np


# ----------------------------------------------------------------------------- PNG IO
def save_png(path, arr):
    a = np.asarray(arr, dtype=np.float32)
    if a.ndim == 2:
        a = a[:, :, None]
    h, w, c = a.shape
    ctype = {1: 0, 3: 2, 4: 6}[c]
    data = (np.clip(a, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)[::-1]  # bottom-up -> top-down
    raw = b"".join(b"\x00" + data[y].tobytes() for y in range(h))

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload +
                struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n" +
           chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, ctype, 0, 0, 0)) +
           chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def srgb(c):
    return np.array(c, dtype=np.float32) / 255.0


# ----------------------------------------------------------------------------- resampling
def downsample2(a):
    """2x box filter (H, W must be even)."""
    return 0.25 * (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2])


def resize_to(a, size):
    """Repeated 2x box downsample until width == size."""
    while a.shape[1] > size:
        a = downsample2(a)
    return a


def blur_wrap(a, r):
    """Separable box blur with wrap-around (tileable), radius r px, 3 passes ~ gaussian."""
    out = a.astype(np.float32)
    for _ in range(3):
        for ax in (0, 1):
            acc = np.zeros_like(out)
            for d in range(-r, r + 1):
                acc += np.roll(out, d, axis=ax)
            out = acc / (2 * r + 1)
    return out


# ----------------------------------------------------------------------------- noise
def fbm(shape, feature_px, rng, octaves=4, gain=0.5, stretch=(1.0, 1.0)):
    """Tileable fractal gaussian noise via spectral filtering of white noise.
    feature_px: size of the largest features; stretch=(sx, sy) >1 elongates features
    along that axis.  Returns roughly zero-mean, unit-ish std field."""
    h, w = shape
    fy = np.fft.fftfreq(h)[:, None] / stretch[1]
    fx = np.fft.fftfreq(w)[None, :] / stretch[0]
    f2 = fx * fx + fy * fy
    total = np.zeros(shape, np.float32)
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        s = feature_px / (2 ** o)
        sig = 1.0 / max(s, 1.0)
        white = rng.standard_normal(shape)
        f = np.real(np.fft.ifft2(np.fft.fft2(white) * np.exp(-f2 / (2 * sig * sig))))
        f = (f - f.mean()) / (f.std() + 1e-8)
        total += amp * f
        norm += amp
        amp *= gain
    return total / norm


def norm01(a):
    lo, hi = np.percentile(a, 0.5), np.percentile(a, 99.5)
    return np.clip((a - lo) / (hi - lo + 1e-8), 0, 1).astype(np.float32)


def worley(shape, cells_x, cells_y, rng, jitter=0.9, warp=None):
    """Tileable worley noise on a jittered grid.  Returns F1, F2 (pixel units) and cell id.
    warp: optional (dx, dy) pixel displacement arrays (must themselves be tileable)."""
    h, w = shape
    cw, ch = w / cells_x, h / cells_y
    jx = rng.random((cells_y, cells_x))
    jy = rng.random((cells_y, cells_x))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    if warp is not None:
        xx = xx + warp[0]
        yy = yy + warp[1]
    gx = np.floor(xx / cw).astype(np.int64)
    gy = np.floor(yy / ch).astype(np.int64)
    f1 = np.full(shape, 1e9, np.float32)
    f2 = np.full(shape, 1e9, np.float32)
    cid = np.zeros(shape, np.int64)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            ncx, ncy = gx + dx, gy + dy
            mx, my = ncx % cells_x, ncy % cells_y
            px = (ncx + 0.5 + jitter * (jx[my, mx] - 0.5)) * cw
            py = (ncy + 0.5 + jitter * (jy[my, mx] - 0.5)) * ch
            d = np.sqrt((xx - px) ** 2 + (yy - py) ** 2)
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            cid = np.where(closer, my * cells_x + mx, cid)
            f1 = np.where(closer, d, f1)
    return f1, f2, cid


# ----------------------------------------------------------------------------- maps
def normal_from_height(hgt, strength, wrap=True):
    """height (H,W) in px-ish units -> RGB OpenGL normal map (0..1)."""
    if wrap:
        dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5
        dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
    else:
        dy, dx = np.gradient(hgt)
    n = np.dstack([-dx * strength, -dy * strength, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return (n * 0.5 + 0.5).astype(np.float32)


def bleed_colour(rgb, alpha, iters=24):
    """Push opaque colours outward into transparent texels so mipmaps / bilinear filtering
    of alpha cards do not pick up black fringes."""
    a = (alpha > 0.02).astype(np.float32)
    col = rgb * a[..., None]
    wsum = a.copy()
    out = rgb.copy()
    filled = a > 0
    for _ in range(iters):
        col = (col + np.roll(col, 1, 0) + np.roll(col, -1, 0) + np.roll(col, 1, 1) + np.roll(col, -1, 1))
        wsum = (wsum + np.roll(wsum, 1, 0) + np.roll(wsum, -1, 0) + np.roll(wsum, 1, 1) + np.roll(wsum, -1, 1))
        m = wsum > 0
        newly = m & ~filled
        out[newly] = col[newly] / wsum[newly][:, None]
        filled |= m
        col = col / 5.0
        wsum = wsum / 5.0
    out[~filled] = rgb[alpha > 0.02].mean(0) if (alpha > 0.02).any() else 0.0
    return out


# ----------------------------------------------------------------------------- card painter
class Canvas:
    """Supersampled z-buffer painter for alpha cards.

    Elements carry a height z (towards the viewer, metres-ish); the visible element per
    texel is the one with the largest z, which gives believable overlap and a height map
    that turns into the normal map."""

    def __init__(self, w, h, px_per_m, ss=2):
        self.W, self.H, self.ss = w * ss, h * ss, ss
        self.ppm = px_per_m * ss
        self.col = np.zeros((self.H, self.W, 3), np.float32)
        self.hgt = np.full((self.H, self.W), -1e3, np.float32)
        self.rough = np.ones((self.H, self.W), np.float32)
        self.cov = np.zeros((self.H, self.W), bool)
        self._off = {}

    def _offsets(self, rmax):
        k = int(np.ceil(rmax))
        if k not in self._off:
            oy, ox = np.mgrid[-k:k + 1, -k:k + 1]
            m = ox * ox + oy * oy <= (k + 0.5) ** 2
            self._off[k] = (ox[m].astype(np.float32), oy[m].astype(np.float32))
        return self._off[k]

    def _write(self, ix, iy, h, col, rough):
        ok = (ix >= 0) & (ix < self.W) & (iy >= 0) & (iy < self.H)
        ix, iy, h, col, rough = ix[ok], iy[ok], h[ok], col[ok], rough[ok]
        idx = iy * self.W + ix
        order = np.argsort(h, kind="stable")              # highest written last wins
        idx, h, col, rough = idx[order], h[order], col[order], rough[order]
        hflat = self.hgt.reshape(-1)
        win = h > hflat[idx]
        idx, h, col, rough = idx[win], h[win], col[win], rough[win]
        hflat[idx] = h
        self.col.reshape(-1, 3)[idx] = col
        self.rough.reshape(-1)[idx] = rough
        self.cov.reshape(-1)[idx] = True

    def capsules(self, p0, p1, r0, r1, z0, z1, col, rough, shade_tip=0.0, chunk=4000):
        """Draw N tapered capsules.  p0/p1 (N,2) metres in card space (x right, y up),
        r0/r1 radii (m), z0/z1 heights (m), col (N,3) sRGB 0..1, rough (N,)."""
        p0 = np.atleast_2d(p0).astype(np.float32)
        p1 = np.atleast_2d(p1).astype(np.float32)
        n = len(p0)
        bc = lambda v: np.broadcast_to(np.asarray(v, np.float32), (n,)).copy()
        r0, r1, z0, z1, rough = bc(r0), bc(r1), bc(z0), bc(z1), bc(rough)
        col = np.broadcast_to(np.asarray(col, np.float32), (n, 3))
        for s in range(0, n, chunk):
            sl = slice(s, s + chunk)
            self._caps(p0[sl], p1[sl], r0[sl], r1[sl], z0[sl], z1[sl], col[sl], rough[sl], shade_tip)

    def _caps(self, p0, p1, r0, r1, z0, z1, col, rough, shade_tip):
        cx, cy = self.W / 2.0, 0.0
        a = p0 * self.ppm + [cx, cy]
        b = p1 * self.ppm + [cx, cy]
        ra, rb = np.maximum(r0 * self.ppm, 0.6), np.maximum(r1 * self.ppm, 0.6)
        L = np.linalg.norm(b - a, axis=1)
        ns = np.maximum(2, np.ceil(L / 0.7).astype(np.int64))
        seg = np.repeat(np.arange(len(a)), ns)
        start = np.repeat(np.cumsum(ns) - ns, ns)
        t = ((np.arange(seg.size) - start) / (np.repeat(ns, ns) - 1)).astype(np.float32)
        pts = a[seg] + (b[seg] - a[seg]) * t[:, None]
        rad = ra[seg] + (rb[seg] - ra[seg]) * t
        zz = z0[seg] + (z1[seg] - z0[seg]) * t
        ox, oy = self._offsets(rad.max())
        dist = np.sqrt(ox * ox + oy * oy)
        inside = dist[None, :] <= rad[:, None] + 0.25
        si, oi = np.nonzero(inside)
        ix = np.floor(pts[si, 0] + ox[oi]).astype(np.int64)
        iy = np.floor(pts[si, 1] + oy[oi]).astype(np.int64)
        rr = rad[si] / self.ppm
        prof = np.sqrt(np.clip(1.0 - (dist[oi] / (rad[si] + 0.25)) ** 2, 0, 1))
        h = zz[si] + rr * prof
        c = col[seg[si]] * (1.0 - shade_tip * (1 - t[si]))[:, None] if shade_tip else col[seg[si]]
        c = c * (0.82 + 0.18 * prof)[:, None]
        self._write(ix, iy, h, c, rough[seg[si]])

    def polygon_leaf(self, base, direction, length, width, z, col, rough, tilt=1.0,
                     serr=0.06, shape=0.55, vein_col=None):
        """Rasterise one ovate/triangular serrated leaf. base (2,), direction unit (2,)."""
        ppm = self.ppm
        d = np.asarray(direction, np.float32)
        nrm = np.array([-d[1], d[0]], np.float32)
        bx, by = base[0] * ppm + self.W / 2.0, base[1] * ppm
        Lp, Wp = length * ppm, width * ppm * max(tilt, 0.15)
        ext = Lp + Wp
        x0, x1 = int(max(bx - ext, 0)), int(min(bx + ext, self.W - 1))
        y0, y1 = int(max(by - ext, 0)), int(min(by + ext, self.H - 1))
        if x1 <= x0 or y1 <= y0:
            return
        yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1].astype(np.float32)
        rx, ry = xx - bx, yy - by
        s = (rx * d[0] + ry * d[1]) / Lp            # 0 base .. 1 tip
        q = (rx * nrm[0] + ry * nrm[1]) / Wp         # -0.5 .. 0.5 half widths
        prof = np.where(s > 0, (np.clip(s, 0, 1) ** shape) * (1 - np.clip(s, 0, 1)) ** 0.9, 0)
        prof = prof / ((shape / (shape + 0.9)) ** shape * (0.9 / (shape + 0.9)) ** 0.9)
        teeth = 1.0 - serr * (0.5 + 0.5 * np.sin(s * 60.0)) ** 2
        half = 0.5 * prof * teeth
        m = (s >= 0) & (s <= 1) & (np.abs(q) <= half)
        if not m.any():
            return
        qq = np.abs(q[m]) / np.maximum(half[m], 1e-4)
        dome = (1 - qq * qq) * 0.002 * tilt
        sm = s[m]
        vein = np.exp(-(q[m] / 0.025) ** 2) * 0.0006
        side = np.abs(np.sin((sm * 9.0 - np.abs(q[m]) * 14.0) * np.pi))
        sidev = (side > 0.92) * 0.0003
        h = z + dome - vein - sidev + 0.004 * sm * (1 - sm)
        c = np.broadcast_to(np.asarray(col, np.float32), (m.sum(), 3)) * (0.86 + 0.14 * (1 - qq))[:, None]
        if vein_col is not None:
            vm = (vein > 0.0003) | (sidev > 0)
            c = np.where(vm[:, None], np.asarray(vein_col, np.float32), c)
        self._write(xx[m].astype(np.int64), yy[m].astype(np.int64), h,
                    c, np.full(m.sum(), rough, np.float32))

    def finish(self, normal_strength=1.0, ao=0.45):
        """Returns dict of final-resolution maps: albedo_rgba, normal, rough, alpha."""
        cov = self.cov.astype(np.float32)
        hg = np.where(self.cov, self.hgt, np.nan)
        lo = np.nanpercentile(hg, 2) if self.cov.any() else 0
        hi = np.nanpercentile(hg, 98) if self.cov.any() else 1
        hn = np.clip((np.nan_to_num(hg, nan=lo) - lo) / (hi - lo + 1e-9), 0, 1)
        col = self.col * ((1 - ao) + ao * hn)[..., None]
        hpx = np.where(self.cov, self.hgt * self.ppm, np.nan)
        hpx = np.nan_to_num(hpx, nan=np.nanmin(hpx) if self.cov.any() else 0)
        alpha = cov
        rough = self.rough
        while alpha.shape[1] > self.W // self.ss:
            col = downsample2(col * alpha[..., None])
            hpx = downsample2(hpx)
            rough = downsample2(rough * alpha)
            alpha = downsample2(alpha)
            col = col / np.maximum(alpha, 1e-4)[..., None]
            rough = rough / np.maximum(alpha, 1e-4)
        hpx = hpx / self.ss
        col = bleed_colour(np.clip(col, 0, 1), alpha)
        nrm = normal_from_height(hpx, normal_strength, wrap=False)
        flat = alpha < 0.02
        nrm[flat] = (0.5, 0.5, 1.0)
        rough = np.where(flat, 0.8, rough)
        rgba = np.dstack([col, alpha])
        return {"albedo": rgba, "normal": nrm, "rough": np.clip(rough, 0, 1), "alpha": alpha}
