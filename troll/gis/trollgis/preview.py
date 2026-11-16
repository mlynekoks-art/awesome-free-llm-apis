"""Preview images for visual QA (hillshade tinted by terrain class)."""
from __future__ import annotations
import numpy as np
import rasterio
from PIL import Image
from . import codec
from .config import REPORTS, SECTORS_DIR, world
from .grid import parse_id
from .tiles import load_chunks

TINT = {1: (118, 140, 84), 2: (72, 104, 62), 3: (128, 116, 96), 4: (138, 138, 140), 5: (96, 98, 104),
        6: (236, 240, 244), 7: (190, 220, 232), 8: (196, 184, 150), 9: (96, 84, 70), 13: (44, 78, 112), 14: (60, 96, 124)}


def sector_arrays(sid: str) -> tuple[np.ndarray, np.ndarray]:
    """Rebuild full-sector height + material rasters (north-up) from the encoded chunks."""
    s = parse_id(sid)
    cm = world()["grid"]["chunk_m"]
    h = np.empty((s.size, s.size), np.float32)
    m = np.empty((s.size, s.size), np.uint8)
    for name, blob in load_chunks(sid).items():
        ci, cj = int(name[:2]), int(name[3:])
        q, mm = codec.decode(blob)
        rows = slice(s.size - (cj + 1) * cm, s.size - cj * cm)
        h[rows, ci * cm:(ci + 1) * cm] = codec.dequantise(q[1:-1, 1:-1])[::-1]
        m[rows, ci * cm:(ci + 1) * cm] = mm[1:-1, 1:-1][::-1]
    return h, m


def render(h: np.ndarray, m: np.ndarray, scale: int = 4) -> Image.Image:
    gy, gx = np.gradient(h.astype(np.float64))
    shade = np.clip(0.62 + (gx - gy) * 0.33, 0.12, 1.25)
    rgb = np.zeros(h.shape + (3,), np.float32)
    for code, col in TINT.items():
        rgb[m == code] = col
    rgb *= shade[..., None]
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    return img.resize((h.shape[1] // scale, h.shape[0] // scale), Image.LANCZOS)


def sector_preview(sid: str) -> str:
    out = REPORTS / "previews" / f"{sid}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    render(*sector_arrays(sid)).save(out, quality=88)
    return str(out)


def mosaic(sids: list[str], name: str, scale: int = 8) -> str:
    secs = [parse_id(s) for s in sids]
    c0, c1 = min(s.col for s in secs), max(s.col for s in secs)
    r0, r1 = min(s.row for s in secs), max(s.row for s in secs)
    size = secs[0].size
    H = np.zeros(((r1 - r0 + 1) * size, (c1 - c0 + 1) * size), np.float32)
    M = np.full(H.shape, 13, np.uint8)
    for s in secs:
        h, m = sector_arrays(s.id)
        ys = slice((r1 - s.row) * size, (r1 - s.row + 1) * size)
        xs = slice((s.col - c0) * size, (s.col - c0 + 1) * size)
        H[ys, xs], M[ys, xs] = h, m
    out = REPORTS / "previews" / f"{name}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    render(H, M, scale).save(out, quality=88)
    return str(out)
