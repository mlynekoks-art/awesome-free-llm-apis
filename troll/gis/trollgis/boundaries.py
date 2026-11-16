"""National / county boundaries (Kartverket 'Administrative enheter', WFS app:Fylke).

County polygons include territorial sea, so they are used as a NATIONAL mask
(to drop the Swedish/Finnish/Russian border strips that the DTM also covers) and
to tag each sector with its county. The land/sea split itself comes from the DTM.
"""
from __future__ import annotations
import geopandas as gpd
import numpy as np
import requests
from rasterio import features
from rasterio.transform import from_origin
from .config import CACHE, DATA, world
from .grid import realm_bounds

WFS = "https://wfs.geonorge.no/skwms1/wfs.administrative_enheter"
PATH = DATA / "boundaries" / "fylker_25833.gpkg"


def download_fylker() -> gpd.GeoDataFrame:
    raw = CACHE / "wfs" / "fylke.gml"
    if not raw.exists():
        raw.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(WFS, params={"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                                      "typeNames": "app:Fylke", "srsName": "urn:ogc:def:crs:EPSG::25833"}, timeout=600)
        r.raise_for_status()
        raw.write_bytes(r.content)
    g = gpd.read_file(raw)[["fylkesnummer", "fylkesnavn", "oppdateringsdato", "geometry"]]
    g["fylkesnummer"] = g["fylkesnummer"].astype(int)
    g["oppdateringsdato"] = g["oppdateringsdato"].astype(str)
    PATH.parent.mkdir(parents=True, exist_ok=True)
    g.to_file(PATH, driver="GPKG")
    return g


def load_fylker() -> gpd.GeoDataFrame:
    return gpd.read_file(PATH) if PATH.exists() else download_fylker()


def county_raster(realm: str = "MAINLAND") -> np.ndarray:
    """County number per L0 cell (0 = outside Norway)."""
    res = world()["lod"]["L0"]["res_m"]
    b = realm_bounds(realm)
    shape = ((b[3] - b[1]) // res, (b[2] - b[0]) // res)
    g = load_fylker()
    return features.rasterize(zip(g.geometry, g.fylkesnummer), out_shape=shape,
                              transform=from_origin(b[0], b[3], res, res), fill=0, dtype="int16")
