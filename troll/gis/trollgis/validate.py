"""Automated GIS checks (these run on data, NOT inside a running Roblox session).

  codec      - every chunk decodes back to the quantised source, max error <= step/2
  seams      - chunk halo cells equal the neighbouring chunk's edge cells (inside a sector)
  sector_seam- a sector's stored edge equals an independent re-download of the same strip
  holes      - no NaN / nodata / out-of-range cells
  landmarks  - known summit heights vs the DEM
"""
from __future__ import annotations
import numpy as np
import rasterio
from . import codec, registry
from .config import SECTORS_DIR, world
from .grid import parse_id, sector_at
from .tiles import load_chunks
from .wcs import read_dem


def validate_sector(sid: str) -> dict:
    w = world()
    s = parse_id(sid)
    step = w["height_encoding"]["step_m"]
    chunks = load_chunks(sid)
    cm = w["grid"]["chunk_m"]
    k = s.size // cm
    with rasterio.open(SECTORS_DIR / sid / "dem_1m.tif") as ds:
        dem = ds.read(1)
    res = {"sector": sid, "checks": {}}
    max_err, dec = 0.0, {}
    land_cells = 0
    for name, blob in chunks.items():
        q, m = codec.decode(blob)
        dec[name] = (q, m)
        ci, cj = int(name[:2]), int(name[3:])
        src = dem[s.size - (cj + 1) * cm: s.size - cj * cm, ci * cm:(ci + 1) * cm][::-1]
        h = codec.dequantise(q[1:-1, 1:-1])
        land = m[1:-1, 1:-1] != 13
        land_cells += int(land.sum())
        if land.any():
            max_err = max(max_err, float(np.abs(h - src)[land].max()))
    res["checks"]["codec_roundtrip"] = {"max_abs_error_m": round(max_err, 4), "tolerance_m": step / 2 + 1e-4,
                                        "land_cells": land_cells, "pass": max_err <= step / 2 + 1e-4}
    worst = 0
    for cj in range(k):
        for ci in range(k):
            q, _ = dec[f"{ci:02d}_{cj:02d}"]
            if ci + 1 < k:
                qe, _ = dec[f"{ci + 1:02d}_{cj:02d}"]
                worst = max(worst, int(np.abs(q[1:-1, -1] - qe[1:-1, 1]).max()), int(np.abs(q[1:-1, -2] - qe[1:-1, 0]).max()))
            if cj + 1 < k:
                qn, _ = dec[f"{ci:02d}_{cj + 1:02d}"]
                worst = max(worst, int(np.abs(q[-1, 1:-1] - qn[1, 1:-1]).max()), int(np.abs(q[-2, 1:-1] - qn[0, 1:-1]).max()))
    res["checks"]["chunk_seams"] = {"max_mismatch_steps": worst, "pass": worst == 0}
    res["checks"]["holes"] = {"nan": int(np.isnan(dem).sum()), "min_m": float(dem.min()), "max_m": float(dem.max()),
                              "pass": bool(np.isfinite(dem).all() and dem.min() > -50 and dem.max() < 2500)}
    # independent re-download of a strip straddling the east edge (bypasses the stored raster)
    e0, n0, e1, n1 = s.bounds
    strip = read_dem(s.realm, (e1 - 2, n0 + 1000, e1 + 2, n0 + 1500), 1.0)
    mine = dem[s.size - 1500: s.size - 1000, -2:]
    d = float(np.abs(strip[:, :2] - mine).max())
    q, _ = dec[f"{k - 1:02d}_{1000 // cm:02d}"]
    halo = codec.dequantise(q[1:-1, -1])[::-1]
    land = np.abs(strip[:cm, 2][-cm:]) > 1e-3
    seg = strip[500 - cm:, 2]  # rows for chunk cj=4 (n0+1000..n0+1250) are the LAST cm rows of the strip
    land = np.abs(seg) > 1e-3
    d2 = float(np.abs(halo - seg)[land].max()) if land.any() else 0.0
    res["checks"]["sector_edge_vs_redownload"] = {"core_max_diff_m": round(d, 4), "halo_vs_neighbour_cells_max_diff_m": round(d2, 4),
                                                  "pass": d < 1e-3 and d2 <= step / 2 + 1e-4}
    res["result"] = "PASS" if all(c["pass"] for c in res["checks"].values()) else "FAIL"
    meta = registry.load_meta(sid)
    meta["validation"] = res
    registry.save_meta(meta)
    return res


# Official heights (Kartverket / Norgeskart, m above sea level, NN2000 where published)
LANDMARKS = [
    ("Galdhøpiggen", 8.3123, 61.6364, 2469),
    ("Glittertind", 8.5572, 61.6511, 2452),
    ("Store Skagastølstind", 7.8719, 61.4614, 2405),
    ("Snøhetta", 9.2733, 62.3197, 2286),
    ("Store Trolltind (Romsdalen)", 7.7269, 62.4860, 1788),
    ("Romsdalshornet", 7.7936, 62.4878, 1550),
    ("Gaustatoppen", 8.6561, 59.8542, 1883),
    ("Stetind", 16.3414, 68.1650, 1392),
    ("Preikestolen", 6.1903, 58.9864, 604),
]


def validate_landmarks(radius_m: int = 250) -> list[dict]:
    from pyproj import Transformer
    t = Transformer.from_crs(4326, 25833, always_xy=True)
    out = []
    for name, lon, lat, official in LANDMARKS:
        e, n = t.transform(lon, lat)
        e, n = round(e), round(n)
        a = read_dem("MAINLAND", (e - radius_m, n - radius_m, e + radius_m, n + radius_m), 1.0)
        iy, ix = np.unravel_index(int(a.argmax()), a.shape)
        out.append({"name": name, "official_m": official, "dem_max_m": round(float(a.max()), 2),
                    "diff_m": round(float(a.max()) - official, 2), "sector": sector_at("MAINLAND", e, n).id,
                    "peak_e": e - radius_m + ix, "peak_n": n + radius_m - iy})
    return out
