"""L0 country model: a 250 m DEM of the whole realm, used for the land mask,
the global sector index and (later) the far-horizon / map mesh."""
from __future__ import annotations
import numpy as np
import rasterio
from rasterio.transform import from_origin
from .config import DATA, world
from .grid import realm_bounds
from .wcs import read_dem

# Extent actually served by the national DTM (from WCS DescribeCoverage), snapped inward to 1 km.
MAINLAND_DEM_EXTENT = (-100000, 6400000, 1150000, 8000000)


def overview_path(realm: str):
    return DATA / "overview" / f"{realm.lower()}_L0_250m.tif"


def build_overview(realm: str = "MAINLAND") -> np.ndarray:
    res = world()["lod"]["L0"]["res_m"]
    b = realm_bounds(realm)
    w, h = (b[2] - b[0]) // res, (b[3] - b[1]) // res
    full = np.zeros((h, w), np.float32)
    ext = MAINLAND_DEM_EXTENT
    data = read_dem(realm, ext, res, interpolation="bilinear")
    x0 = (ext[0] - b[0]) // res
    y0 = (b[3] - ext[3]) // res
    full[y0:y0 + data.shape[0], x0:x0 + data.shape[1]] = data
    full[np.abs(full) < 0.01] = 0.0
    path = overview_path(realm)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", driver="GTiff", height=h, width=w, count=1, dtype="float32",
                       crs=f"EPSG:{world()['realms'][realm]['epsg']}", transform=from_origin(b[0], b[3], res, res),
                       compress="deflate", predictor=3, tiled=True) as ds:
        ds.write(full, 1)
    return full


def load_overview(realm: str = "MAINLAND") -> np.ndarray:
    with rasterio.open(overview_path(realm)) as ds:
        return ds.read(1)
