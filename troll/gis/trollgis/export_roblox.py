"""Write a sector's encoded chunks as Luau ModuleScripts + a Rojo project that
builds a standalone place file for that sector (base game code + sector data)."""
from __future__ import annotations
import json
from . import codec, registry
from .config import ROOT, world
from .tiles import load_chunks

BUILD = ROOT / "roblox" / "build"


def export_sector(sid: str) -> dict:
    meta = registry.load_meta(sid)
    chunks = load_chunks(sid)
    out = BUILD / "sectors" / sid
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.luau"):
        old.unlink()
    for name, blob in chunks.items():
        (out / f"c_{name}.luau").write_text(f'return "{codec.to_b64(blob)}"\n')
    w = world()
    manifest = {"id": sid, "realm": meta["realm"], "epsg": meta["bounds_epsg"], "bounds": meta["bounds"],
                "centre": meta["centre"], "sectorMetres": w["grid"]["sector_m"], "chunkMetres": w["grid"]["chunk_m"],
                "studsPerMetre": w["scale"]["studs_per_metre"], "heightOffset": w["height_encoding"]["offset_m"],
                "heightStep": w["height_encoding"]["step_m"], "elevation": meta["elevation"],
                "materialSource": meta["material_source"],
                "latitude": meta["latitude"], "longitude": meta["longitude"]}
    (out / "Manifest.json").write_text(json.dumps(manifest, indent=1))
    base = json.loads((ROOT / "roblox" / "default.project.json").read_text())
    base["name"] = f"Troll_{sid}"

    def rebase(node):
        for key, val in node.items():
            if key == "$path":
                node[key] = "../" + val
            elif isinstance(val, dict):
                rebase(val)
    rebase(base["tree"])
    base["tree"]["ServerStorage"]["TrollSectorData"] = {"$className": "Folder", sid: {"$path": f"sectors/{sid}"}}
    proj = BUILD / f"{sid}.project.json"
    proj.write_text(json.dumps(base, indent=1))
    meta["status"] = "EXPORTED"
    meta["roblox_export"] = {"project": str(proj.relative_to(ROOT)), "place": f"roblox/build/Troll_{sid}.rbxl"}
    registry.save_meta(meta)
    return meta
