"""Global sector registry.

`data/registry/<realm>_sectors.csv` is the country-wide index (one row per sector
that contains land). Per-sector production state lives in
`data/sectors/<id>/sector.json`; `sync()` folds that state back into the index so
finished sectors are never regenerated or overwritten by accident.
"""
from __future__ import annotations
import csv
import json
from datetime import datetime, timezone
import numpy as np
from .config import REGISTRY_DIR, SECTORS_DIR, world
from .grid import Sector, parse_id
from .overview import load_overview

FIELDS = ["id", "realm", "region", "col", "row", "min_e", "min_n", "max_e", "max_n", "class", "fylke", "land_frac",
          "l0_min_m", "l0_max_m", "l0_mean_m", "status", "lod", "validation", "approval", "sources", "updated"]
STATUSES = ["PENDING", "DEM_READY", "EXPORTED", "IMPORTED_IN_STUDIO", "DRESSED", "ACCEPTED"]


def index_path(realm: str):
    return REGISTRY_DIR / f"{realm.lower()}_sectors.csv"


def build_index(realm: str = "MAINLAND") -> list[dict]:
    w = world()
    from .boundaries import county_raster, load_fylker
    ov = load_overview(realm)
    county = county_raster(realm)
    names = dict(zip(load_fylker().fylkesnummer, load_fylker().fylkesnavn))
    k = w["grid"]["sector_m"] // w["lod"]["L0"]["res_m"]
    r = w["realms"][realm]
    rows = []
    for row in range(r["rows"]):
        # raster row 0 is the northern edge
        y1 = ov.shape[0] - row * k
        for col in range(r["cols"]):
            cell = ov[y1 - k:y1, col * k:(col + 1) * k]
            cc = county[y1 - k:y1, col * k:(col + 1) * k]
            land = (cell > 0) & (cc > 0)          # Norwegian land only
            frac = float(land.mean())
            if frac == 0:
                continue
            nat = float((cc > 0).mean())
            vals, cnt = np.unique(cc[land], return_counts=True)
            fylke = names[int(vals[cnt.argmax()])].split(" - ")[0]
            s = Sector(realm, col, row)
            b = s.bounds
            rows.append({"id": s.id, "realm": realm, "region": s.region_id, "col": col, "row": row,
                         "min_e": b[0], "min_n": b[1], "max_e": b[2], "max_n": b[3],
                         "class": "LAND" if frac == 1 else ("BORDER" if nat < 1 else "COAST"), "fylke": fylke, "land_frac": round(frac, 3),
                         "l0_min_m": round(float(cell[land].min()), 1), "l0_max_m": round(float(cell[land].max()), 1),
                         "l0_mean_m": round(float(cell[land].mean()), 1), "status": "PENDING", "lod": "L0",
                         "validation": "", "approval": "NOT_SUBMITTED", "sources": "kartverket-nhm-dtm", "updated": ""})
    write_index(realm, rows)
    return rows


def read_index(realm: str = "MAINLAND") -> list[dict]:
    with open(index_path(realm), newline="") as fh:
        return list(csv.DictReader(fh))


def write_index(realm: str, rows: list[dict]) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    with open(index_path(realm), "w", newline="") as fh:
        wr = csv.DictWriter(fh, FIELDS)
        wr.writeheader()
        wr.writerows(rows)


def sector_meta_path(sid: str):
    return SECTORS_DIR / sid / "sector.json"


def load_meta(sid: str) -> dict | None:
    p = sector_meta_path(sid)
    return json.loads(p.read_text()) if p.exists() else None


def save_meta(meta: dict) -> None:
    meta["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    p = sector_meta_path(meta["id"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(meta, indent=1))


def sync(realm: str = "MAINLAND") -> dict:
    """Fold per-sector state into the global index and return status counts."""
    rows = read_index(realm)
    by_id = {r["id"]: r for r in rows}
    if SECTORS_DIR.exists():
        for d in sorted(SECTORS_DIR.iterdir()):
            meta = load_meta(d.name)
            if meta and meta["id"] in by_id and parse_id(meta["id"]).realm == realm:
                r = by_id[meta["id"]]
                r.update(status=meta["status"], lod=meta["lod"], validation=meta.get("validation", {}).get("result", ""),
                         approval=meta.get("approval", "NOT_SUBMITTED"), updated=meta["updated"],
                         sources=";".join(meta.get("sources", [])))
    write_index(realm, rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts
