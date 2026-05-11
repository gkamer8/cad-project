"""Design parameters for the server-rack shelf.

EIA-310 reference values (1U height, rail hole-to-hole horizontal pitch, etc.)
live here as module-level constants and are reused by ``model.py``. All
dimensions are millimeters unless suffixed otherwise.
"""
from dataclasses import dataclass
from typing import Final


RACK_UNIT_MM: Final[float] = 44.45
RAIL_HOLE_PITCH_HORIZONTAL_MM: Final[float] = 465.1
RACK_FACE_WIDTH_MM: Final[float] = 482.6


@dataclass(frozen=True)
class ShelfParams:
    height_u: int
    depth_mm: float
    thickness_mm: float


SHELF_1U_CANTILEVER = ShelfParams(
    height_u=1,
    depth_mm=250.0,
    thickness_mm=2.0,
)
