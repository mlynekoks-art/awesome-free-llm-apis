"""Cross-language test: export fixtures for a sector and run the Luau decoder /
voxel planner under Lune (outside Roblox Studio)."""
from __future__ import annotations
import json
import subprocess
import sys
from . import codec, registry
from .config import REPORTS, ROOT, world
from .tiles import load_chunks


def run(sid: str, names: list[str]) -> int:
    chunks = load_chunks(sid)
    manifest = json.loads((ROOT / "roblox" / "build" / "sectors" / sid / "Manifest.json").read_text())
    cases = []
    for name in names:
        q, m = codec.decode(chunks[name])
        cases.append({"name": name, "ci": int(name[:2]), "cj": int(name[3:]), "payload": codec.to_b64(chunks[name]),
                      "heights": [round(v, 4) for v in codec.dequantise(q).ravel().tolist()], "materials": m.ravel().tolist()})
    fx = ROOT / "data" / "cache" / f"fixture_{sid}.json"
    fx.parent.mkdir(parents=True, exist_ok=True)
    fx.write_text(json.dumps({"manifest": manifest, "chunks": cases}))
    out = REPORTS / f"luau_test_{sid}.json"
    return subprocess.call(["lune", "run", str(ROOT / "roblox/tests/test_terrain.luau"), str(ROOT), str(fx), str(out)])


if __name__ == "__main__":
    sys.exit(run(sys.argv[1], sys.argv[2:]))
