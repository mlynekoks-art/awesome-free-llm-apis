"""Elevation download from the Kartverket national height model (WCS 1.0.0).

Requests are cut into pieces below the server's size limit, cached on disk as
GeoTIFF and retried with backoff. Pixel edges sit on whole metres in EPSG:25833,
so any bbox on whole metres at res 1 returns native, un-resampled cells.
"""
from __future__ import annotations
import hashlib
import time
from pathlib import Path
import numpy as np
import rasterio
import requests
from .config import CACHE, world

SESSION = requests.Session()
SESSION.headers["User-Agent"] = "trollgis/0.1"


def _fetch(dem: dict, bbox, width: int, height: int, interpolation: str) -> np.ndarray:
    key = hashlib.sha1(f"{dem['coverage']}|{bbox}|{width}x{height}|{interpolation}".encode()).hexdigest()[:20]
    path = CACHE / "wcs" / f"{key}.tif"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        params = {"service": "WCS", "version": "1.0.0", "request": "GetCoverage", "coverage": dem["coverage"],
                  "crs": "EPSG:25833", "bbox": ",".join(str(v) for v in bbox), "width": width, "height": height,
                  "format": "GeoTIFF", "interpolation": interpolation}
        last = None
        for attempt in range(5):
            try:
                r = SESSION.get(dem["url"], params=params, timeout=180)
                if r.status_code == 200 and r.content[:2] in (b"II", b"MM"):
                    tmp = path.with_suffix(".part")
                    tmp.write_bytes(r.content)
                    tmp.rename(path)
                    break
                last = f"HTTP {r.status_code}: {r.content[:200]!r}"
            except requests.RequestException as exc:  # network hiccup: back off and retry
                last = repr(exc)
            time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f"WCS download failed for bbox {bbox}: {last}")
    with rasterio.open(path) as ds:
        arr = ds.read(1)
    if arr.shape != (height, width):
        raise RuntimeError(f"WCS returned {arr.shape}, expected {(height, width)} for {bbox}")
    return arr


def read_dem(realm: str, bbox, res_m: float, interpolation: str = "nearest neighbor") -> np.ndarray:
    """Return float32 heights (metres), north-up, for bbox=(min_e,min_n,max_e,max_n) at res_m."""
    dem = world()["realms"][realm]["dem"]
    if dem["type"] != "wcs":
        raise NotImplementedError(f"No DEM source wired for realm {realm} yet: {dem.get('note')}")
    min_e, min_n, max_e, max_n = bbox
    w = round((max_e - min_e) / res_m)
    h = round((max_n - min_n) / res_m)
    out = np.empty((h, w), np.float32)
    step_x = min(dem["max_width"], 2000)
    step_y = min(dem["max_height"], 2000)
    for y0 in range(0, h, step_y):
        y1 = min(h, y0 + step_y)
        for x0 in range(0, w, step_x):
            x1 = min(w, x0 + step_x)
            sub = (min_e + x0 * res_m, max_n - y1 * res_m, min_e + x1 * res_m, max_n - y0 * res_m)
            out[y0:y1, x0:x1] = _fetch(dem, sub, x1 - x0, y1 - y0, interpolation)
    return out
