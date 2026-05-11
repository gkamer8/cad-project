"""cq-studio entry point. Run with `uv run cq-studio projects/server_rack_shelf/viewer.py`."""
from projects.server_rack_shelf.model import build_bracket, build_top
from projects.server_rack_shelf.params import (
    RAIL_HOLE_PITCH_HORIZONTAL_MM,
    SHELF_1U_CANTILEVER,
)


def main():
    bracket = build_bracket(SHELF_1U_CANTILEVER.bracket)
    top = build_top(SHELF_1U_CANTILEVER.top)

    rail_x = RAIL_HOLE_PITCH_HORIZONTAL_MM / 2
    top_z = SHELF_1U_CANTILEVER.top.thickness_mm / 2

    return {
        "left_bracket": bracket.translate((-rail_x, 0, 0)),
        "right_bracket": bracket.translate((rail_x, 0, 0)),
        "top": top.translate((0, 0, top_z)),
    }
