"""Build the server-rack shelf and export it as STEP."""
from pathlib import Path

import cadquery as cq

from projects.server_rack_shelf.model import build_shelf
from projects.server_rack_shelf.params import SHELF_1U_CANTILEVER


EXPORT_PATH = Path(__file__).parent / "exports" / "shelf.step"

shelf = build_shelf(SHELF_1U_CANTILEVER)
cq.exporters.export(shelf, str(EXPORT_PATH))
print(f"wrote {EXPORT_PATH}")
