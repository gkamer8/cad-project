"""CadQuery model for the server-rack shelf."""
import cadquery as cq

from projects.server_rack_shelf.params import RACK_FACE_WIDTH_MM, ShelfParams


def build_shelf(params: ShelfParams) -> cq.Workplane:
    return cq.Workplane("XY").box(
        RACK_FACE_WIDTH_MM,
        params.depth_mm,
        params.thickness_mm,
    )
