"""R-1 area rug."""

from ..geom.prims import superellipsoid
from ..spec import RUG
from .kit import part_at
from .parts import Group, Mat, Part, Shading


def rug_parts() -> list[Part]:
    w, d, h = RUG.size
    slab = superellipsoid((w, d, 2 * h), 0.08, 0.04, 6, 64)
    return [part_at("rug", [slab], RUG.placements, Mat.RUG, Group.SOFT_GOODS, Shading.SOFT)]
