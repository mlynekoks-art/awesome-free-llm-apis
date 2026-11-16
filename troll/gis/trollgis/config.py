"""World configuration loader. Single source of truth: troll/config/world.json."""
from __future__ import annotations
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "world.json"
DATA = ROOT / "data"
CACHE = DATA / "cache"
REGISTRY_DIR = DATA / "registry"
SECTORS_DIR = DATA / "sectors"
ROBLOX_SECTORS = ROOT / "roblox" / "sectors"
REPORTS = ROOT / "reports"


@lru_cache(maxsize=1)
def world() -> dict:
    return json.loads(CONFIG_PATH.read_text())
