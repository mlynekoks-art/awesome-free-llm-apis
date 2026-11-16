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
    water_bad, lake_err = 0, 0.0
    land_cells = 0
    for name, blob in chunks.items():
        q, m, wq = codec.decode(blob)
        dec[name] = (q, m)
        wet = wq[1:-1, 1:-1] >= 0
        if wet.any():   # water surface must never be below its bed
            water_bad += int((wq[1:-1, 1:-1][wet] < q[1:-1, 1:-1][wet]).sum())
            lk = m[1:-1, 1:-1] == 14
            if lk.any():   # lake surface level must equal the flat DTM surface
                srcl = dem[s.size - (int(name[3:]) + 1) * cm: s.size - int(name[3:]) * cm, int(name[:2]) * cm:(int(name[:2]) + 1) * cm][::-1]
                lake_err = max(lake_err, float(np.abs(codec.dequantise(wq[1:-1, 1:-1][lk]) - srcl[lk]).max()))
        ci, cj = int(name[:2]), int(name[3:])
        src = dem[s.size - (cj + 1) * cm: s.size - cj * cm, ci * cm:(ci + 1) * cm][::-1]
        h = codec.dequantise(q[1:-1, 1:-1])
        land = (m[1:-1, 1:-1] != 13) & (m[1:-1, 1:-1] != 14)
        land_cells += int(land.sum())
        if land.any():
            max_err = max(max_err, float(np.abs(h - src)[land].max()))
    res["checks"]["codec_roundtrip"] = {"max_abs_error_m": round(max_err, 4), "tolerance_m": step / 2 + 1e-4,
                                        "land_cells": land_cells, "pass": max_err <= step / 2 + 1e-4}
    res["checks"]["water"] = {"cells_surface_below_bed": water_bad, "lake_level_vs_dtm_max_diff_m": round(lake_err, 3),
                              "pass": water_bad == 0 and lake_err <= 0.15}
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
    land = (np.abs(seg) > 1e-3) & (dec[f"{k - 1:02d}_{1000 // cm:02d}"][1][1:-1, -1][::-1] < 13)
    d2 = float(np.abs(halo - seg)[land].max()) if land.any() else 0.0
    res["checks"]["sector_edge_vs_redownload"] = {"core_max_diff_m": round(d, 4), "halo_vs_neighbour_cells_max_diff_m": round(d2, 4),
                                                  "pass": d < 1e-3 and d2 <= step / 2 + 1e-4}
    res["result"] = "PASS" if all(c["pass"] for c in res["checks"].values()) else "FAIL"
    meta = registry.load_meta(sid)
    meta["validation"] = res
    registry.save_meta(meta)
    return res


# Official summit heights (m a.s.l.). Positions: Kartverket Stedsnavn API representation
# points (EPSG:25833) where noted "SSR"; otherwise converted from published lon/lat.
# radius = search window for the DEM maximum (representation points are not exact summits).
LANDMARKS = [
    ("Galdhøpiggen (SSR)", 146001, 6851889, 2469, 250),
    ("Glittertind", 159087, 6852208, 2452, 250),
    ("Store Skagastølstind", 120610, 6834953, 2405, 250),
    ("Snøhetta, Dovre (SSR)", 203191, 6922976, 2286, 400),
    ("Store Trolltind, Romsdalen", 126000, 6950000, 1788, 2000),
    ("Romsdalshornet (SSR)", 128807, 6949681, 1550, 300),
    ("Gaustatoppen (SSR)", 144572, 6652234, 1883, 400),
    ("Stetinden, Narvik (SSR)", 566098, 7562126, 1392, 400),
]


def validate_landmarks() -> list[dict]:
    out = []
    for name, e, n, official, radius_m in LANDMARKS:
        a = read_dem("MAINLAND", (e - radius_m, n - radius_m, e + radius_m, n + radius_m), 1.0)
        iy, ix = np.unravel_index(int(a.argmax()), a.shape)
        out.append({"name": name, "official_m": official, "dem_max_m": round(float(a.max()), 2),
                    "diff_m": round(float(a.max()) - official, 2), "search_radius_m": radius_m,
                    "peak_e": int(e - radius_m + ix), "peak_n": int(n + radius_m - iy),
                    "sector": sector_at("MAINLAND", e - radius_m + ix, n + radius_m - iy).id})
    return out


def validate_neighbours(sid: str) -> list[dict]:
    """Cross-sector seam test: this sector's halo cells must equal the neighbour's own edge cells
    (both taken from the ENCODED chunks, i.e. exactly what Roblox will receive)."""
    w = world()
    s = parse_id(sid)
    cm = w["grid"]["chunk_m"]
    k = s.size // cm
    out = []
    mine = load_chunks(sid)
    for side, nb in s.neighbours().items():
        if registry.load_meta(nb.id) is None:
            continue
        theirs = load_chunks(nb.id)
        worst = 0
        cells = 0
        for i in range(k):
            if side == "E":
                a = codec.decode(mine[f"{k - 1:02d}_{i:02d}"])[0][1:-1, -1]
                b = codec.decode(theirs[f"00_{i:02d}"])[0][1:-1, 1]
            elif side == "W":
                a = codec.decode(mine[f"00_{i:02d}"])[0][1:-1, 0]
                b = codec.decode(theirs[f"{k - 1:02d}_{i:02d}"])[0][1:-1, -2]
            elif side == "N":
                a = codec.decode(mine[f"{i:02d}_{k - 1:02d}"])[0][-1, 1:-1]
                b = codec.decode(theirs[f"{i:02d}_00"])[0][1, 1:-1]
            else:
                a = codec.decode(mine[f"{i:02d}_00"])[0][0, 1:-1]
                b = codec.decode(theirs[f"{i:02d}_{k - 1:02d}"])[0][-2, 1:-1]
            worst = max(worst, int(np.abs(a - b).max()))
            cells += a.size
        out.append({"sector": sid, "side": side, "neighbour": nb.id, "edge_cells": cells,
                    "max_mismatch_m": round(worst * w["height_encoding"]["step_m"], 3), "pass": worst == 0})
    return out
