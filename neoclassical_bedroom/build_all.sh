#!/usr/bin/env bash
# Regenerate every deliverable.
# Usage: PY=/path/to/python3.11 GLTF_TRANSFORM=/path/to/gltf-transform ./build_all.sh
set -euo pipefail
cd "$(dirname "$0")"
"$PY" -I tools/fetch_assets.py
"$PY" render_views.py --shots HERO PLAN BED DOOR_WALL EVENING CANOPY --samples 128 --width 1920 --out output/renders
"$PY" build_cad.py --out output/cad --previews output/sheets
"$PY" export_3d.py --out output/cad
"$PY" build_report.py --renders output/renders --cad output/cad --out output --previews output/report/previews
"$PY" build_site.py --gltf-transform "$GLTF_TRANSFORM"
