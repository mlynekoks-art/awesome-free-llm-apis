"""Sector builder: 1 m DEM -> sea mask -> materials -> encoded 250 m chunks (L2).

A HALO of cells around the sector is downloaded so that slope, the synthetic
seabed and each chunk's 1-cell border are computed from real neighbouring data.
Adjacent sectors therefore agree exactly on their shared edge without any
blending step: both read the same national grid cells.
"""
from __future__ import annotations
import json
import numpy as np
import rasterio
from rasterio.transform import from_origin
from scipy import ndimage
from . import codec, materials, registry
from .config import SECTORS_DIR, world
from .grid import Sector
from .wcs import read_dem

HALO = 40  # metres; must exceed the seabed ramp length and the slope kernel


def fetch_with_halo(sector: Sector) -> np.ndarray:
    e0, n0, e1, n1 = sector.bounds
    size = sector.size
    full = np.empty((size + 2 * HALO, size + 2 * HALO), np.float32)
    full[HALO:-HALO, HALO:-HALO] = read_dem(sector.realm, (e0, n0, e1, n1), 1.0)
    full[:HALO, :] = read_dem(sector.realm, (e0 - HALO, n1, e1 + HALO, n1 + HALO), 1.0)       # north strip
    full[-HALO:, :] = read_dem(sector.realm, (e0 - HALO, n0 - HALO, e1 + HALO, n0), 1.0)      # south strip
    full[HALO:-HALO, :HALO] = read_dem(sector.realm, (e0 - HALO, n0, e0, n1), 1.0)            # west strip
    full[HALO:-HALO, -HALO:] = read_dem(sector.realm, (e1, n0, e1 + HALO, n1), 1.0)           # east strip
    return full


def derive(sector: Sector, full: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (surface heights incl. synthetic seabed, material codes, sea mask) for the halo grid."""
    w = world()
    sea = np.abs(full) < 1e-3
    # ignore specks: the sea is a large connected zero-height body
    lab, n = ndimage.label(sea)
    if n:
        sizes = ndimage.sum(sea, lab, range(1, n + 1))
        sea = np.isin(lab, np.flatnonzero(sizes >= 400) + 1)
    gy, gx = np.gradient(full.astype(np.float64))
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    e0, n0, e1, n1 = sector.bounds
    northing = (n1 + HALO - 0.5 - np.arange(full.shape[0]))[:, None] * np.ones((1, full.shape[1]))
    mat = materials.classify(full, slope, sea, northing)
    h = full.astype(np.float64).copy()
    if sea.any():
        dist = ndimage.distance_transform_edt(sea)
        depth = np.minimum(-w["sea"]["placeholder_seabed_m"], 0.6 + dist * 0.3)
        h[sea] = -depth[sea]
    return h, mat, sea


def build_sector(sector: Sector, force: bool = False) -> dict:
    w = world()
    sid = sector.id
    meta = registry.load_meta(sid)
    if meta and meta["status"] not in ("PENDING",) and not force:
        return meta
    out = SECTORS_DIR / sid
    out.mkdir(parents=True, exist_ok=True)
    full = fetch_with_halo(sector)
    h, mat, sea = derive(sector, full)
    core = slice(HALO, -HALO)
    e0, n0, e1, n1 = sector.bounds
    with rasterio.open(out / "dem_1m.tif", "w", driver="GTiff", height=sector.size, width=sector.size, count=1,
                       dtype="float32", crs=f"EPSG:{w['realms'][sector.realm]['epsg']}",
                       transform=from_origin(e0, n1, 1, 1), compress="deflate", predictor=3, tiled=True) as ds:
        ds.write(full[core, core], 1)
    q = codec.quantise(h)
    cm = w["grid"]["chunk_m"]
    k = sector.size // cm
    chunks = {}
    total = 0
    for cj in range(k):          # cj counts north from the south edge
        for ci in range(k):      # ci counts east from the west edge
            r1 = HALO + sector.size - cj * cm + 1     # exclusive raster row just south of chunk + halo cell
            r0 = r1 - cm - 2
            c0 = HALO + ci * cm - 1
            qs = q[r0:r1, c0:c0 + cm + 2][::-1]       # flip so row 0 = south
            ms = mat[r0:r1, c0:c0 + cm + 2][::-1]
            blob = codec.encode(qs, ms)
            chunks[f"{ci:02d}_{cj:02d}"] = blob
            total += len(blob)
    np.save(out / "chunks.npy", np.array([chunks], dtype=object), allow_pickle=True)
    hc = full[core, core]
    from pyproj import Transformer
    lonlat = Transformer.from_crs(w["realms"][sector.realm]["epsg"], 4326, always_xy=True).transform(*sector.centre)
    names, counts = np.unique(mat[core, core], return_counts=True)
    inv = {v: n for n, v in materials.CODES.items()}
    meta = {"id": sid, "realm": sector.realm, "region": sector.region_id, "col": sector.col, "row": sector.row,
            "bounds_epsg": w["realms"][sector.realm]["epsg"], "bounds": [e0, n0, e1, n1], "centre": list(sector.centre),
            "longitude": round(lonlat[0], 5), "latitude": round(lonlat[1], 5),
            "status": "DEM_READY", "lod": "L2",
            "elevation": {"min_m": round(float(hc.min()), 2), "max_m": round(float(hc.max()), 2),
                          "mean_m": round(float(hc.mean()), 2), "source_res_m": 1.0},
            "sea_frac": round(float(sea[core, core].mean()), 4),
            "materials": {inv[int(n)]: round(float(c) / hc.size, 4) for n, c in zip(names, counts)},
            "material_source": "interim-dem-derived", "hydrography": "sea mask from DTM only (lakes/rivers pending NVE/N50)",
            "roads_buildings": "pending (NVDB / N50)", "bathymetry": "synthetic placeholder",
            "chunks": {"count": k * k, "cells": cm, "halo_cells": 1, "encoded_bytes": total},
            "sources": ["kartverket-nhm-dtm-1m (WCS nhm_dtm_topo_25833)"], "validation": {}, "approval": "NOT_SUBMITTED"}
    registry.save_meta(meta)
    return meta


def load_chunks(sid: str) -> dict[str, bytes]:
    return np.load(SECTORS_DIR / sid / "chunks.npy", allow_pickle=True)[0]
