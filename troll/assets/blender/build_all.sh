#!/usr/bin/env bash
# Regenerates every PRODUCED candidate asset (textures, LOD meshes, FBX/GLB, stats, renders).
# Usage: BLENDER=/opt/blender/blender bash troll/assets/blender/build_all.sh
set -euo pipefail
B="${BLENDER:-/opt/blender/blender}"
S="$(cd "$(dirname "$0")/scripts" && pwd)"
"$B" -b -P "$S/gen_spruce.py" -- --force-tex
"$B" -b -P "$S/gen_pine.py" -- --force-tex
"$B" -b -P "$S/gen_boulder.py"
# NOT YET RUN / UNTESTED (birch was not produced in the first candidate session):
# "$B" -b -P "$S/gen_birch.py" -- --force-tex
