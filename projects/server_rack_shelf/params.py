"""Design parameters for the server-rack shelf.

EIA-310 reference values live at module scope as ``Final`` constants and
are reused by ``model.py``. Per-part geometry is captured in frozen
dataclasses; ``ShelfDesign`` groups the bracket and top params together
with the nominal rack depth so a single named instance describes a
complete shelf in its installation context.

All dimensions are millimeters.
"""
from dataclasses import dataclass
from typing import Final


RACK_UNIT_MM: Final[float] = 44.45
RAIL_HOLE_PITCH_HORIZONTAL_MM: Final[float] = 465.1
RACK_FACE_WIDTH_MM: Final[float] = 482.6

# Within a 1U flange centered vertically on its rack slot, the two
# usable EIA-310 hole centers sit symmetrically at +/- this offset from
# the slot's vertical midpoint.
EIA_HOLE_Z_OFFSET_MM: Final[float] = 15.875


@dataclass(frozen=True)
class BracketParams:
    thickness_mm: float
    width_mm: float
    flange_height_mm: float
    arm_length_mm: float
    mount_hole_diameter_mm: float
    slot_length_mm: float
    slot_center_y_mm: float


@dataclass(frozen=True)
class TopParams:
    thickness_mm: float
    depth_mm: float
    width_mm: float
    mount_hole_diameter_mm: float
    front_hole_y_mm: float
    rear_slot_center_y_mm: float
    rear_slot_length_mm: float


@dataclass(frozen=True)
class ShelfDesign:
    bracket: BracketParams
    top: TopParams
    rack_depth_mm: float


SHELF_1U_4POST = ShelfDesign(
    bracket=BracketParams(
        thickness_mm=2.0,
        width_mm=30.0,
        flange_height_mm=RACK_UNIT_MM,
        arm_length_mm=250.0,
        mount_hole_diameter_mm=7.0,
        slot_length_mm=40.0,
        slot_center_y_mm=200.0,
    ),
    top=TopParams(
        thickness_mm=2.0,
        depth_mm=700.0,
        width_mm=482.0,
        mount_hole_diameter_mm=7.0,
        front_hole_y_mm=200.0,
        rear_slot_center_y_mm=500.0,
        rear_slot_length_mm=80.0,
    ),
    rack_depth_mm=700.0,
)
