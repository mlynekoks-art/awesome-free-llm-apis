"""Hydrography and ice from NVE (kart.nve.no ArcGIS REST, EPSG:25833, NLOD).

Lakes: Innsjødatabase polygons (1:20 000-50 000) are only used as SEEDS. The real
shoreline is taken from the 1 m DTM: the lake is the set of cells near the polygon
whose height equals the lake's water level (the DTM is flat on water). This keeps
shores consistent with the terrain to the metre.
"""
from __future__ import annotations
import hashlib
import json
import time
import numpy as np
import requests
from rasterio import features
from rasterio.transform import from_origin
from scipy import ndimage
from shapely.geometry import shape
from .config import CACHE
from .wcs import read_dem

BASE = "https://kart.nve.no/enterprise/rest/services"
LAKES = "Innsjodatabase2/MapServer/5"
GLACIERS = "Bre2/MapServer/9"


def query(layer: str, bbox) -> list[dict]:
    key = hashlib.sha1(f"{layer}|{bbox}".encode()).hexdigest()[:20]
    path = CACHE / "nve" / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    feats, offset = [], 0
    while True:
        params = {"geometry": ",".join(str(v) for v in bbox), "geometryType": "esriGeometryEnvelope", "inSR": 25833,
                  "outSR": 25833, "spatialRel": "esriSpatialRelIntersects", "outFields": "*", "f": "geojson",
                  "resultOffset": offset, "resultRecordCount": 1000, "orderByFields": "objectid"}
        last = None
        for attempt in range(5):
            try:
                r = requests.get(f"{BASE}/{layer}/query", params=params, timeout=120)
                d = r.json()
                if "features" in d:
                    break
                last = str(d)[:200]
            except (requests.RequestException, ValueError) as exc:
                last = repr(exc)
            time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f"NVE query failed for {layer} {bbox}: {last}")
        feats += d["features"]
        if len(d["features"]) < 1000:
            break
        offset += 1000
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(feats))
    return feats


def _raster(geoms, shape_, west: float, north: float) -> np.ndarray:
    if not geoms:
        return np.zeros(shape_, np.int32)
    return features.rasterize(geoms, out_shape=shape_, transform=from_origin(west, north, 1, 1), fill=0, dtype="int32")


def lakes(full: np.ndarray, west: float, north: float, tol_m: float = 0.12, grow_m: int = 25):
    """Return (lake_id raster, {id: info}) for the halo grid whose NW corner is (west, north)."""
    h, w = full.shape
    feats = query(LAKES, (west, north - h, west + w, north))
    ids = np.zeros(full.shape, np.int32)
    info = {}
    for i, f in enumerate(feats, start=1):
        if not f.get("geometry"):
            continue
        seed = _raster([(shape(f["geometry"]), 1)], full.shape, west, north) > 0
        if not seed.any():
            continue
        # Water level: sampled from a small DTM patch around a fixed interior point of the WHOLE
        # polygon, so every sector window that touches this lake derives exactly the same level.
        geom = shape(f["geometry"])
        pt = geom.representative_point()
        px, py = int(pt.x // 1), int(pt.y // 1)
        patch = read_dem("MAINLAND", (px - 32, py - 32, px + 32, py + 32), 1.0)
        inside = _raster([(geom, 1)], patch.shape, px - 32, py + 32) > 0
        bins = np.rint(patch[inside if inside.sum() >= 25 else np.ones_like(inside)] / 0.05).astype(np.int64)
        vals, cnt = np.unique(bins, return_counts=True)
        level = float(vals[cnt.argmax()] * 0.05)
        # Membership is a purely LOCAL rule (no connected-component step), so neighbouring sectors
        # classify shared cells identically: flat at the lake level and within grow_m of the polygon.
        mask = (np.abs(full - level) <= tol_m) & ndimage.binary_dilation(seed, iterations=grow_m)
        # reject seeds that do not sit on flat water in the DTM (drained/regulated lakes, bad polygons)
        if cnt.max() < 0.3 * bins.size:
            info[i] = {"name": f["properties"].get("navn"), "vatnlnr": f["properties"].get("vatnlnr"), "status": "REJECTED_NOT_FLAT",
                       "nve_height_m": f["properties"].get("hoyde")}
            continue
        ids[mask & (ids == 0)] = i
        info[i] = {"name": f["properties"].get("navn"), "vatnlnr": f["properties"].get("vatnlnr"), "status": "OK",
                   "level_m": round(level, 2), "nve_height_m": f["properties"].get("hoyde"),
                   "cells_in_window": int(mask.sum()), "nve_polygon_cells_in_window": int(seed.sum())}
    return ids, info


def glaciers(shape_, west: float, north: float) -> np.ndarray:
    feats = query(GLACIERS, (west, north - shape_[0], west + shape_[1], north))
    return _raster([(shape(f["geometry"]), 1) for f in feats if f.get("geometry")], shape_, west, north) > 0
