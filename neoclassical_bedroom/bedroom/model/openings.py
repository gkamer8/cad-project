"""Windows (6-over-6 double-hung with cased openings) and the pilastered doorcase."""

import numpy as np

from ..geom.mesh import Mesh, merge
from ..geom.prims import box, lathe, loft, prism, smooth_turning, sweep
from ..spec import (
    CASING_W, CHAIR_RAIL_TOP, DOORCASE_TOP, PILASTER_PROJ, PILASTER_W, REVEAL, Opening,
    OpeningKind, OPENINGS,
)
from . import profiles
from .parts import Group, Mat, Part, Shading
from .shell import on_wall

FRAME = 0.75  # window frame member width
FRAME_Y = (-4.75, -1.25)  # window frame depth band inside the wall (wall-local y)
CASING_PROJ = 1.18
UP = (0, 0, 1)
OUT = (0, 1, 0)  # wall-local direction into the room


def _rect_frame(u0, u1, z0, z1, widths, y0, y1) -> list[Mesh]:
    """Four boxes forming a rectangular frame; widths = (left, right, bottom, top)."""
    wl, wr, wb, wt = widths
    return [
        box((u0, y0, z0), (u0 + wl, y1, z1)),
        box((u1 - wr, y0, z0), (u1, y1, z1)),
        box((u0 + wl, y0, z0), (u1 - wr, y1, z0 + wb)),
        box((u0 + wl, y0, z1 - wt), (u1 - wr, y1, z1)),
    ]


def _sash(u0, u1, z0, z1, rails: tuple[float, float], y0, y1) -> tuple[list[Mesh], Mesh]:
    """Sash with 3 x 2 lites; returns (wood members, glass)."""
    stile = 2.0
    wood = _rect_frame(u0, u1, z0, z1, (stile, stile, rails[0], rails[1]), y0, y1)
    gu0, gu1, gz0, gz1 = u0 + stile, u1 - stile, z0 + rails[0], z1 - rails[1]
    mid_y0, mid_y1 = y0 + 0.2, y1 - 0.2
    for k in (1, 2):
        uc = gu0 + (gu1 - gu0) * k / 3
        wood.append(box((uc - 0.375, mid_y0, gz0), (uc + 0.375, mid_y1, gz1)))
    zc = (gz0 + gz1) / 2
    cuts = [gu0] + [gu0 + (gu1 - gu0) * k / 3 + side * 0.375 for k in (1, 2) for side in (-1, 1)] + [gu1]
    wood += [box((a, mid_y0, zc - 0.375), (b, mid_y1, zc + 0.375)) for a, b in zip(cuts[0::2], cuts[1::2])]
    glass = box((gu0, (y0 + y1) / 2 - 0.06, gz0), (gu1, (y0 + y1) / 2 + 0.06, gz1))
    return wood, glass


def _u_path(u_left, u_right, depth, z) -> np.ndarray:
    """Plan path wrapping a block's front (returns to the wall at both ends)."""
    return np.array([[u_left, 0, z], [u_left, depth, z], [u_right, depth, z], [u_right, 0, z]], dtype=float)


def window_parts(w: Opening) -> list[Part]:
    u0, u1, z0, z1 = w.u0, w.u1, w.bottom, w.top
    frame = _rect_frame(u0, u1, z0, z1, (FRAME,) * 4, *FRAME_Y)
    inner_u0, inner_u1, inner_z0, inner_z1 = u0 + FRAME, u1 - FRAME, z0 + FRAME, z1 - FRAME
    meet = (inner_z0 + inner_z1) / 2
    upper_wood, upper_glass = _sash(inner_u0, inner_u1, meet - 0.6, inner_z1, (1.25, 2.0), -3.9, -2.6)
    lower_wood, lower_glass = _sash(inner_u0, inner_u1, inner_z0, meet + 0.6, (2.75, 1.25), -2.5, -1.2)
    lift = box((u0 + 10.0, -1.35, inner_z0 + 1.0), (u0 + 13.0, -0.95, inner_z0 + 1.6))
    lift2 = lift.moved((u1 - u0 - 23.0, 0, 0))
    lock = box(((u0 + u1) / 2 - 1.2, -2.55, meet + 0.6), ((u0 + u1) / 2 + 1.2, -1.6, meet + 1.0))
    ul, ur = u0 - REVEAL, u1 + REVEAL
    casing_path = np.array([[ul, 0, CHAIR_RAIL_TOP], [ul, 0, z1 + REVEAL], [ur, 0, z1 + REVEAL],
                            [ur, 0, CHAIR_RAIL_TOP]], dtype=float)
    casing = sweep(profiles.CASING, casing_path, OUT, closed=False)
    outer_l, outer_r = ul - CASING_W, ur + CASING_W
    stool = box((outer_l - 0.75, -1.25, CHAIR_RAIL_TOP - 1.0), (outer_r + 0.75, 1.9, CHAIR_RAIL_TOP))
    apron_z = CHAIR_RAIL_TOP - 1.0
    apron = sweep(profiles.CASING, np.array([[outer_r - 0.5, 0, apron_z], [outer_l + 0.5, 0, apron_z]]), OUT,
                  closed=False)
    cap = sweep(profiles.HEAD_CAP, _u_path(outer_l, outer_r, CASING_PROJ, z1 + REVEAL + CASING_W), UP,
                closed=False)
    tag = w.tag.lower()
    return [
        Part(f"{tag}_sashes", on_wall(merge(frame + upper_wood + lower_wood), w.wall), Mat.TRIM_IVORY,
             Group.OPENINGS, Shading.EASED),
        Part(f"{tag}_glass", on_wall(merge([upper_glass, lower_glass]), w.wall), Mat.GLASS, Group.OPENINGS,
             Shading.FLAT),
        Part(f"{tag}_hardware", on_wall(merge([lift, lift2, lock]), w.wall), Mat.BRASS, Group.OPENINGS,
             Shading.EASED),
        Part(f"{tag}_casing", on_wall(merge([casing, apron, cap]), w.wall), Mat.TRIM_IVORY, Group.MILLWORK,
             Shading.CRISP),
        Part(f"{tag}_stool", on_wall(stool, w.wall), Mat.TRIM_IVORY, Group.MILLWORK, Shading.EASED),
    ]


def fluted_section(u0: float, u1: float, depth: float, flutes: int) -> np.ndarray:
    """Counter-clockwise (u, y) outline of a pilaster shaft with concave flutes on its face."""
    pts = [(u0, 0.0), (u1, 0.0), (u1, depth)]
    margin = 0.55
    pitch = (u1 - u0 - 2 * margin) / flutes
    radius = pitch * 0.36
    for k in range(flutes):
        uc = u1 - margin - pitch * (k + 0.5)
        t = np.linspace(0, np.pi, 9)
        pts.append((uc + radius, depth))
        pts.extend(zip(uc + radius * np.cos(t), depth - radius * 0.8 * np.sin(t)))
        pts.append((uc - radius, depth))
    pts.append((u0, depth))
    return np.asarray(pts)


def _panel_door(u0, u1, z0, z1) -> tuple[list[Mesh], list[Mesh]]:
    """Six-panel door: (slab + stiles/rails, raised panel fields)."""
    face, recess, field_y = -0.75, -1.05, -0.82
    slab = box((u0, -2.5, z0), (u1, recess, z1))
    stile, mid = 4.75, 4.5
    rails = [(z0, 9.5), (30.5, 38.0), (60.0, 64.5), (z1 - 4.75, z1)]
    frame = [box((u0, recess, z0), (u0 + stile, face, z1)), box((u1 - stile, recess, z0), (u1, face, z1)),
             box(((u0 + u1 - mid) / 2, recess, z0), ((u0 + u1 + mid) / 2, face, z1))]
    cm0, cm1 = (u0 + u1 - mid) / 2, (u0 + u1 + mid) / 2  # rails stop at the centre stile (no overlaps)
    frame += [box((u0 + stile, recess, a), (cm0, face, b)) for a, b in rails]
    frame += [box((cm1, recess, a), (u1 - stile, face, b)) for a, b in rails]
    fields = []
    columns = [(u0 + stile, (u0 + u1 - mid) / 2), ((u0 + u1 + mid) / 2, u1 - stile)]
    for (_, top), (bottom, _) in zip(rails[:-1], rails[1:]):
        for a, b in columns:
            # rings run counter-clockwise for a viewer in the room so the loft faces outward
            outer = np.array([[a, recess, bottom], [b, recess, bottom], [b, recess, top], [a, recess, top]])
            inner = np.array([[a + 1.6, field_y, bottom - 1.6], [b - 1.6, field_y, bottom - 1.6],
                              [b - 1.6, field_y, top + 1.6], [a + 1.6, field_y, top + 1.6]])
            fields.append(loft(np.stack([outer, inner])))
    return [slab] + frame, fields


def door_parts(d: Opening) -> list[Part]:
    u0, u1 = d.u0, d.u1
    left = (u0 - REVEAL - PILASTER_W, u0 - REVEAL)
    right = (u1 + REVEAL, u1 + REVEAL + PILASTER_W)
    trim, gilt = [], []
    for a, b in (left, right):
        trim.append(box((a - 0.25, 0.0, 0.0), (b + 0.25, PILASTER_PROJ + 0.5, 7.5)))
        trim.append(sweep(profiles.PILASTER_BASE, _u_path(a, b, PILASTER_PROJ, 7.5), UP, closed=False))
        trim.append(prism(fluted_section(a, b, PILASTER_PROJ, 5), 9.25, 77.0))
        trim.append(sweep(profiles.PILASTER_CAPITAL, _u_path(a, b, PILASTER_PROJ, 77.0), UP, closed=False))
    ea, eb = left[0] - 0.25, right[1] + 0.25
    trim.append(box((ea, 0.0, 79.75), (eb, 1.5, 82.25)))  # architrave
    trim.append(box((ea + 0.25, 0.0, 82.25), (eb - 0.25, 1.25, 85.0)))  # frieze
    trim.append(sweep(profiles.ENTABLATURE_CORNICE, _u_path(ea, eb, 1.5, 85.0), UP, closed=False))
    trim.append(box((ea, 0.0, DOORCASE_TOP - 0.25), (eb, 3.9, DOORCASE_TOP)))
    patera = [(0.05, 0.0), (1.5, 0.0), (1.5, 0.12), (1.2, 0.3), (0.7, 0.42), (0.05, 0.48)]
    for uc in ((left[0] + left[1]) / 2, (u0 + u1) / 2, (right[0] + right[1]) / 2):
        disc = lathe(patera, 24, lambda th, z: 1.0 - 0.12 * (np.abs(np.cos(4 * th)) ** 0.6) * (z > 0.1))
        gilt.append(disc.transformed(_wall_face_matrix(uc, 83.6, 1.25)))
    leaf, fields = _panel_door(u0 + 0.125, u1 - 0.125, 0.5, d.top - 0.125)
    stops = [box((u0, -0.75, 0.0), (u0 + 0.5, -0.25, d.top)), box((u1 - 0.5, -0.75, 0.0), (u1, -0.25, d.top)),
             box((u0, -0.75, d.top - 0.5), (u1, -0.25, d.top))]
    knob = lathe([(0.05, 0.0), (1.25, 0.0), (1.25, 0.15), (0.35, 0.35), (0.3, 1.6), (0.9, 1.9), (1.05, 2.4),
                  (0.8, 2.75), (0.05, 2.85)], 28, smooth_turning)
    hardware = [knob.transformed(_wall_face_matrix(u1 - 2.75, 36.0, -0.75))]
    escutcheon = lathe([(0.05, 0.0), (0.55, 0.0), (0.5, 0.12), (0.05, 0.14)], 20, smooth_turning)
    hardware.append(escutcheon.transformed(_wall_face_matrix(u1 - 2.75, 32.5, -0.75)))
    for z in (8.0, 40.0, 72.0):
        hardware.append(lathe([(0.05, z - 2.0), (0.32, z - 2.0), (0.32, z + 2.0), (0.05, z + 2.0)], 16,
                              smooth_turning).moved((u0 + 0.05, -0.5, 0.0)))
    return [
        Part("d1_doorcase", on_wall(merge(trim), d.wall), Mat.TRIM_IVORY, Group.MILLWORK, Shading.CRISP),
        Part("d1_paterae", on_wall(merge(gilt), d.wall), Mat.GILT, Group.MILLWORK, Shading.CRISP),
        Part("d1_leaf", on_wall(merge(leaf + stops), d.wall), Mat.TRIM_IVORY, Group.OPENINGS, Shading.EASED),
        Part("d1_panels", on_wall(merge(fields), d.wall), Mat.TRIM_IVORY, Group.OPENINGS, Shading.FLAT),
        Part("d1_hardware", on_wall(merge(hardware), d.wall), Mat.BRASS, Group.OPENINGS, Shading.CRISP),
    ]


def _wall_face_matrix(u: float, z: float, depth: float) -> np.ndarray:
    """Local lathe axis (+z) -> wall-local +y (pointing into the room) at (u, depth, z)."""
    m = np.eye(4)
    m[:3, 0] = (1, 0, 0)
    m[:3, 1] = (0, 0, -1)
    m[:3, 2] = (0, 1, 0)
    m[:3, 3] = (u, depth, z)
    return m


def opening_parts() -> list[Part]:
    parts = []
    for o in OPENINGS:
        parts.extend(window_parts(o) if o.kind is OpeningKind.WINDOW else door_parts(o))
    return parts
