"""Terrain material classes shared by the Python pipeline and the Luau importer
(roblox/src/shared/TerrainMaterials.luau must list the same codes).

The current classification is INTERIM: derived from elevation, slope and the sea
mask only. It will be replaced by NIBIO AR5/SR16 + N50 land cover per sector;
`material_source` in sector.json records which one a sector was built with."""
from __future__ import annotations
import numpy as np

CODES = {"GRASS": 1, "LEAFY_GRASS": 2, "GROUND": 3, "ROCK": 4, "SLATE": 5, "SNOW": 6, "GLACIER": 7,
         "SAND": 8, "MUD": 9, "SEA": 13, "LAKE": 14}


def treeline_m(northing: np.ndarray | float) -> np.ndarray | float:
    """Approximate climatic forest line: ~1150 m at 59N falling to ~250 m at 71N (linear fit, interim)."""
    return np.clip(1150.0 - (np.asarray(northing) - 6_560_000) * (900.0 / 1_340_000), 150.0, 1200.0)


def classify(h: np.ndarray, slope_deg: np.ndarray, sea: np.ndarray, northing: np.ndarray) -> np.ndarray:
    tl = treeline_m(northing)
    m = np.full(h.shape, CODES["LEAFY_GRASS"], np.uint8)       # forest floor below the tree line
    m[h > tl - 150] = CODES["GRASS"]                            # birch belt / open heath
    m[h > tl + 100] = CODES["GROUND"]                           # alpine heath, thin soil
    m[h > tl + 550] = CODES["ROCK"]                             # high alpine block fields
    m[slope_deg > 32] = CODES["GROUND"]                         # scree and thin soil
    m[slope_deg > 42] = CODES["ROCK"]
    m[slope_deg > 62] = CODES["SLATE"]                          # near-vertical walls
    m[(h < 1.5) & ~sea & (slope_deg < 8)] = CODES["SAND"]       # shoreline strip
    m[sea] = CODES["SEA"]
    return m
