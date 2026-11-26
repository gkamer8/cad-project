"""Pleated drapery panels (hourglass tie-backs) and the window treatments."""

from dataclasses import dataclass

import numpy as np

from ..geom.mesh import Mesh, merge
from ..geom.prims import arc, grid, tube
from ..spec import CASING_W, DRAPE_POLE_Z, DRAPE_STACK, DRAPE_TIEBACK_Z, REVEAL, OPENINGS, OpeningKind
from .kit import finial_urn, turned
from .parts import Group, Mat, Part, Shading
from .shell import on_wall


@dataclass(frozen=True)
class Drape:
    """A gathered panel in a local frame: a = across the panel, d = out from its backing, z = up."""

    z_top: float
    z_tie: float
    z_bottom: float
    span_top: tuple[float, float]
    span_tie: tuple[float, float]
    span_bottom: tuple[float, float]
    depth: tuple[float, float, float]  # panel centre-plane offset at top, tie-back, bottom
    fabric_width: float
    folds: int
    seed: int


def _ease(t: np.ndarray, power: float) -> np.ndarray:
    return np.clip(t, 0, 1) ** power


def drape_mesh(dr: Drape) -> Mesh:
    rows = np.linspace(dr.z_top, dr.z_bottom, 72)
    above = rows >= dr.z_tie
    s_up = (dr.z_top - rows) / (dr.z_top - dr.z_tie)
    s_dn = (dr.z_tie - rows) / (dr.z_tie - dr.z_bottom)
    e_up, e_dn = _ease(s_up, 1.7), 1 - (1 - _ease(s_dn, 1.0)) ** 2.2

    def lerp3(top, tie, bottom):
        top, tie, bottom = (np.asarray(v, float) for v in (top, tie, bottom))
        return np.where(above[:, None], top + (tie - top) * e_up[:, None], tie + (bottom - tie) * e_dn[:, None])

    spans = lerp3(dr.span_top, dr.span_tie, dr.span_bottom)
    depth = lerp3([dr.depth[0]], [dr.depth[1]], [dr.depth[2]])[:, 0]
    width = spans[:, 1] - spans[:, 0]
    amp = np.clip((dr.fabric_width - width) / (4.0 * dr.folds) * 0.95, 0.35, 3.2)
    rng = np.random.default_rng(dr.seed)
    cols = dr.folds * 10 + 1
    s = np.linspace(0, 1, cols)
    fold_gain = 0.75 + 0.5 * rng.random(dr.folds + 1)
    gain = np.interp(s * dr.folds, np.arange(dr.folds + 1), fold_gain)
    wobble = 0.35 * np.sin(rows[:, None] * 0.11 + rng.uniform(0, 6)) * np.sin(np.pi * s)[None, :]
    phase = 2 * np.pi * dr.folds * s[None, :] + wobble
    a = spans[:, :1] + width[:, None] * s[None, :]
    d = depth[:, None] + amp[:, None] * gain[None, :] * np.sin(phase)
    z = np.broadcast_to(rows[:, None], a.shape) + 0.25 * np.cos(phase) * (rows[:, None] < dr.z_tie)
    return grid(np.stack([a, d, z], axis=-1), wrap_rows=False, wrap_cols=False)


def mirrored(dr: Drape, center: float) -> Drape:
    flip = lambda span: (2 * center - span[1], 2 * center - span[0])
    return Drape(dr.z_top, dr.z_tie, dr.z_bottom, flip(dr.span_top), flip(dr.span_tie), flip(dr.span_bottom),
                 dr.depth, dr.fabric_width, dr.folds, dr.seed + 17)


def tassel() -> Mesh:
    return turned([(0.05, 0.0), (0.75, 0.0), (1.0, 0.6), (0.95, 2.4), (0.5, 3.0), (0.65, 3.4), (0.55, 4.0),
                   (0.2, 4.3), (0.25, 4.9), (0.05, 5.0)], 24)


def window_panels(index: int, u0: float, u1: float) -> tuple[Drape, Drape]:
    """The pair of drapery panels at a window, in wall-local (u, depth, z)."""
    outer_l = u0 - REVEAL - CASING_W
    left = Drape(
        z_top=DRAPE_POLE_Z - 1.6, z_tie=DRAPE_TIEBACK_Z, z_bottom=0.4,
        span_top=(outer_l - DRAPE_STACK, outer_l + 7.0), span_tie=(outer_l - 9.0, outer_l - 3.0),
        span_bottom=(outer_l - DRAPE_STACK - 0.5, outer_l + 1.5), depth=(3.4, 5.0, 4.2),
        fabric_width=56.0, folds=7, seed=index * 3,
    )
    return left, mirrored(left, (u0 + u1) / 2)


def window_treatment(index: int, u0: float, u1: float) -> tuple[list[Mesh], list[Mesh]]:
    """Two panels + gilt pole, rings, finials and tie-backs in wall-local coordinates."""
    outer_l, outer_r = u0 - REVEAL - CASING_W, u1 + REVEAL + CASING_W
    center = (u0 + u1) / 2
    left, right = window_panels(index, u0, u1)
    panels = [drape_mesh(left), drape_mesh(right)]
    pole_a, pole_b = outer_l - DRAPE_STACK - 3.0, outer_r + DRAPE_STACK + 3.0
    gilt = [tube(np.array([[pole_a, 3.6, DRAPE_POLE_Z], [pole_b, 3.6, DRAPE_POLE_Z]]), 0.65, 20)]
    for end, direction in ((pole_a, -1.0), (pole_b, 1.0)):
        fin = finial_urn(0.85).transformed(_axis_to_u(direction)).moved((end, 3.6, DRAPE_POLE_Z))
        gilt.append(fin)
        bracket = end - direction * 2.0
        gilt.append(tube(np.array([[bracket, 0.0, DRAPE_POLE_Z], [bracket, 3.6, DRAPE_POLE_Z]]), 0.3, 10))
        gilt.append(turned([(0.05, 0.0), (1.1, 0.0), (1.1, 0.25), (0.5, 0.45), (0.05, 0.5)], 24)
                    .transformed(_axis_to_y()).moved((bracket, 0.0, DRAPE_POLE_Z)))
    for span in (left.span_top, right.span_top):
        for u in np.linspace(span[0] + 0.6, span[1] - 0.6, 7):
            ring = arc((0.0, 0.0, 0.0), 0.95, 0, 360, 25)
            gilt.append(tube(np.c_[np.full(25, u), 3.6 + ring[:, 0], DRAPE_POLE_Z + ring[:, 1]], 0.12, 6))
    for tie_u in (outer_l - 6.0, 2 * center - (outer_l - 6.0)):
        loop = np.c_[tie_u + 3.6 * np.cos(np.linspace(0, 2 * np.pi, 33)),
                     5.0 + 2.8 * np.sin(np.linspace(0, 2 * np.pi, 33)), np.full(33, DRAPE_TIEBACK_Z)]
        gilt.append(tube(loop, 0.32, 8))
        gilt.append(tassel().transformed(np.diag([1, 1, -1, 1])).moved((tie_u, 7.9, DRAPE_TIEBACK_Z - 0.3)))
    return panels, gilt


def _axis_to_u(direction: float) -> np.ndarray:
    """Rotate a +z lathe so its axis points along wall-local +u or -u."""
    m = np.eye(4)
    m[:3, :3] = [[0, 0, direction], [0, 1, 0], [-direction, 0, 0]]
    return m


def _axis_to_y() -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]
    return m


def window_drapery_parts() -> list[Part]:
    fabric, gilt = [], []
    for i, o in enumerate([o for o in OPENINGS if o.kind is OpeningKind.WINDOW]):
        panels, metal = window_treatment(i, o.u0, o.u1)
        fabric.extend(on_wall(p, o.wall) for p in panels)
        gilt.extend(on_wall(m, o.wall) for m in metal)
    return [
        Part("drapery_panels", merge(fabric), Mat.SILK_RED, Group.SOFT_GOODS, Shading.SOFT),
        Part("drapery_hardware", merge(gilt), Mat.GILT, Group.SOFT_GOODS, Shading.CRISP),
    ]
