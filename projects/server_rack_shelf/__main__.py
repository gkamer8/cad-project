"""Build the server-rack shelf parts and export each as a STEP file."""
from pathlib import Path

import cadquery as cq

from projects.server_rack_shelf.model import build_bracket, build_top
from projects.server_rack_shelf.params import SHELF_1U_CANTILEVER


EXPORT_DIR = Path(__file__).parent / "exports"

bracket_path = EXPORT_DIR / "bracket.step"
top_path = EXPORT_DIR / "top.step"

cq.exporters.export(build_bracket(SHELF_1U_CANTILEVER.bracket), str(bracket_path))
print(f"wrote {bracket_path}")

cq.exporters.export(build_top(SHELF_1U_CANTILEVER.top), str(top_path))
print(f"wrote {top_path}")
