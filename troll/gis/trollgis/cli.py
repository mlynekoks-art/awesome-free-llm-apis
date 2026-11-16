"""Command line entry point:  python -m trollgis.cli <command>

  overview                 build the L0 250 m country DEM
  index                    build the global sector index from the L0 DEM
  sector <id|E,N> [...]    build + validate + export sectors (skips finished ones)
  batch <n> [--near E,N]   build the next n PENDING sectors (optionally nearest to a point)
  landmarks                compare known summit heights with the DEM
  status                   sync the registry and print counts
"""
from __future__ import annotations
import json
import sys
import time
from . import export_roblox, overview, registry, tiles, validate
from .config import REPORTS
from .grid import parse_id, sector_at


def _resolve(arg: str):
    if "," in arg:
        e, n = (float(v) for v in arg.split(","))
        return sector_at("MAINLAND", e, n)
    return parse_id(arg)


def do_sector(sector) -> dict:
    t = time.time()
    meta = tiles.build_sector(sector)
    res = meta.get("validation") or {}
    if not res:
        res = validate.validate_sector(sector.id)
    if res["result"] == "PASS" and registry.load_meta(sector.id)["status"] == "DEM_READY":
        export_roblox.export_sector(sector.id)
    meta = registry.load_meta(sector.id)
    print(f"{sector.id} {meta['status']} validation={res['result']} elev={meta['elevation']['min_m']}..{meta['elevation']['max_m']} m "
          f"sea={meta['sea_frac']} bytes={meta['chunks']['encoded_bytes']} ({time.time() - t:.0f}s)", flush=True)
    return meta


def main(argv: list[str]) -> None:
    cmd = argv[0] if argv else "status"
    if cmd == "overview":
        a = overview.build_overview()
        print("L0 overview", a.shape, "max", float(a.max()), "land frac", float((a > 0).mean()))
    elif cmd == "index":
        rows = registry.build_index()
        print("sectors with land:", len(rows), "LAND", sum(r["class"] == "LAND" for r in rows))
    elif cmd == "sector":
        for a in argv[1:]:
            do_sector(_resolve(a))
        print(registry.sync())
    elif cmd == "batch":
        n = int(argv[1])
        rows = [r for r in registry.read_index() if r["status"] == "PENDING"]
        if "--near" in argv:
            e, nn = (float(v) for v in argv[argv.index("--near") + 1].split(","))
            rows.sort(key=lambda r: (int(r["min_e"]) + 2000 - e) ** 2 + (int(r["min_n"]) + 2000 - nn) ** 2)
        for r in rows[:n]:
            if registry.load_meta(r["id"]) is None:
                do_sector(parse_id(r["id"]))
        print(registry.sync())
    elif cmd == "landmarks":
        res = validate.validate_landmarks()
        REPORTS.mkdir(exist_ok=True)
        (REPORTS / "landmarks.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
        for r in res:
            print(f"{r['name']:32s} official {r['official_m']:5d}  dem {r['dem_max_m']:8.2f}  diff {r['diff_m']:+.2f}  {r['sector']}")
    elif cmd == "status":
        print(registry.sync())
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
