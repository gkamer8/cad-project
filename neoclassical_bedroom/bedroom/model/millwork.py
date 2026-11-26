"""Wall millwork: baseboard, chair rail, dentil cornice, applied panels and the damask bay."""

import numpy as np

from ..geom.mesh import merge
from ..geom.prims import box, sweep
from ..spec import (
    CHAIR_RAIL_H, CHAIR_RAIL_TOP, CORNICE_BOTTOM, CROWN_BOTTOM, DADO_PANEL, DAMASK_BAY,
    DENTIL_BOTTOM, PANEL_MARGIN, ROOM_L, ROOM_W, UPPER_PANEL, OpeningKind, Wall, openings_on,
    trim_extent, wall_bays,
)
from . import profiles
from .parts import Group, Mat, Part, Shading
from .shell import on_wall

ORDER = (Wall.SOUTH, Wall.EAST, Wall.NORTH, Wall.WEST)  # counter-clockwise, interior on the left
STARTS = np.cumsum([0.0] + [w.value.length for w in ORDER[:-1]])
TOTAL = sum(w.value.length for w in ORDER)
CORNERS = np.concatenate([STARTS, STARTS + TOTAL])


def _xy(s: float) -> np.ndarray:
    s = s % TOTAL
    index = int(np.searchsorted(STARTS, s, side="right")) - 1
    return ORDER[index].value.point(s - STARTS[index])


def _blocked(kinds: tuple[OpeningKind, ...]) -> list[tuple[float, float]]:
    spans = []
    for wall, start in zip(ORDER, STARTS):
        for opening in openings_on(wall):
            e0, e1 = trim_extent(opening)
            spans.extend([(start + e0, start + e1)] if opening.kind in kinds else [])
    return sorted(spans)


def perimeter_runs(kinds: tuple[OpeningKind, ...]) -> list[np.ndarray]:
    """Free stretches of wall between the trim of the given opening kinds, turning corners."""
    spans = _blocked(kinds)
    wrapped = spans[1:] + [(spans[0][0] + TOTAL, spans[0][1] + TOTAL)]
    runs = []
    for (_, start), (end, _) in zip(spans, wrapped):
        inner = [c for c in CORNERS if start < c < end]
        runs.append(np.array([_xy(s) for s in [start, *inner, end]]))
    return runs


def _run_parts(name: str, profile, z: float, kinds, mat: Mat) -> list[Part]:
    meshes = [sweep(profile, np.c_[run, np.full(len(run), z)], (0, 0, 1), closed=False)
              for run in perimeter_runs(kinds)]
    return [Part(name, merge(meshes), mat, Group.MILLWORK, Shading.CRISP)]


def _room_loop(z: float) -> np.ndarray:
    return np.array([[0, 0, z], [ROOM_L, 0, z], [ROOM_L, ROOM_W, z], [0, ROOM_W, z]], dtype=float)


def cornice_parts() -> list[Part]:
    crown = sweep(profiles.CROWN, _room_loop(CROWN_BOTTOM), (0, 0, 1), closed=True)
    band = sweep(profiles.DENTIL_BACK, _room_loop(DENTIL_BOTTOM), (0, 0, 1), closed=True)
    astragal = sweep(profiles.ASTRAGAL, _room_loop(CORNICE_BOTTOM), (0, 0, 1), closed=True)
    dentils = []
    for wall in ORDER:
        for u in np.arange(2.25, wall.value.length - 1.5, 2.0):
            block = box((u - 0.5, 0.45, DENTIL_BOTTOM + 0.05), (u + 0.5, 1.4, CROWN_BOTTOM - 0.02))
            dentils.append(on_wall(block, wall))
    return [
        Part("cornice_crown", merge([crown, band, astragal]), Mat.TRIM_IVORY, Group.MILLWORK, Shading.CRISP),
        Part("cornice_dentils", merge(dentils), Mat.TRIM_IVORY, Group.MILLWORK, Shading.FLAT),
    ]


def frame_path(u0: float, u1: float, z0: float, z1: float) -> np.ndarray:
    """Rectangle on a wall face, ordered so the sweep's 'left' points into the frame."""
    return np.array([[u1, 0, z0], [u0, 0, z0], [u0, 0, z1], [u1, 0, z1]], dtype=float)


def _frame(wall: Wall, profile, u0: float, u1: float, z0: float, z1: float):
    return on_wall(sweep(profile, frame_path(u0, u1, z0, z1), (0, 1, 0), closed=True), wall)


def panel_parts() -> list[Part]:
    upper, dado = [], []
    for wall in Wall:
        for u0, u1 in wall_bays(wall):
            a, b = u0 + PANEL_MARGIN, u1 - PANEL_MARGIN
            dado.append(_frame(wall, profiles.DADO_PANEL, a, b, *DADO_PANEL))
            upper.extend([] if (wall, (u0, u1)) == (Wall.WEST, DAMASK_BAY) else
                         [_frame(wall, profiles.PANEL, a, b, *UPPER_PANEL)])
        for opening in openings_on(wall):
            e0, e1 = trim_extent(opening)
            dado.extend([_frame(wall, profiles.DADO_PANEL, e0 + 1.0, e1 - 1.0, *DADO_PANEL)]
                        if opening.kind is OpeningKind.WINDOW else [])
    return [
        Part("panel_moldings_upper", merge(upper), Mat.TRIM_IVORY, Group.MILLWORK, Shading.CRISP),
        Part("panel_moldings_dado", merge(dado), Mat.TRIM_IVORY, Group.MILLWORK, Shading.CRISP),
    ]


def damask_parts() -> list[Part]:
    """Upholstered silk-damask panel behind the bed, edged with a gilt bead."""
    u0, u1 = DAMASK_BAY[0] + 3.0, DAMASK_BAY[1] - 3.0
    z0, z1 = CHAIR_RAIL_TOP + 2.0, 79.0
    panel = on_wall(box((u0, 0.0, z0), (u1, 0.55, z1)), Wall.WEST)
    edge = _frame(Wall.WEST, profiles.scaled(profiles.GILT_FRAME, 0.55, 0.6), u0 - 1.3, u1 + 1.3, z0 - 1.3, z1 + 6)
    return [
        Part("damask_panel", panel, Mat.DAMASK, Group.MILLWORK, Shading.EASED),
        Part("damask_gilt_edge", edge, Mat.GILT, Group.MILLWORK, Shading.CRISP),
    ]


def millwork_parts() -> list[Part]:
    doors = (OpeningKind.DOOR,)
    every = (OpeningKind.DOOR, OpeningKind.WINDOW)
    return [
        *_run_parts("baseboard", profiles.BASEBOARD, 0.0, doors, Mat.TRIM_IVORY),
        *_run_parts("chair_rail", profiles.CHAIR_RAIL, CHAIR_RAIL_TOP - CHAIR_RAIL_H, every, Mat.TRIM_IVORY),
        *cornice_parts(),
        *panel_parts(),
        *damask_parts(),
    ]
