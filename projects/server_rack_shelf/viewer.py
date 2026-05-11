"""cq-studio entry point. Run with `uv run cq-studio projects/server_rack_shelf/viewer.py`."""
from projects.server_rack_shelf.model import build_bracket, build_top
from projects.server_rack_shelf.params import (
    RAIL_HOLE_PITCH_HORIZONTAL_MM,
    SHELF_1U_4POST,
)


def main():
    bracket = build_bracket(SHELF_1U_4POST.bracket)
    top = build_top(SHELF_1U_4POST.top)

    rail_x = RAIL_HOLE_PITCH_HORIZONTAL_MM / 2
    rack_depth = SHELF_1U_4POST.rack_depth_mm
    top_z = SHELF_1U_4POST.top.thickness_mm / 2

    rear_bracket = bracket.rotate((0, 0, 0), (0, 0, 1), 180)

    return {
        "front_left": bracket.translate((-rail_x, 0, 0)),
        "front_right": bracket.translate((rail_x, 0, 0)),
        "rear_left": rear_bracket.translate((-rail_x, rack_depth, 0)),
        "rear_right": rear_bracket.translate((rail_x, rack_depth, 0)),
        "top": top.translate((0, 0, top_z)),
    }
