"""A-201 / A-202 interior elevations: architecture drawn from the spec and profiles,
furniture from hidden-line silhouettes of the 3D model, all clipped by what sits in front.
"""

import numpy as np
import shapely
from ezdxf.enums import TextEntityAlignment as TA

from ..model import profiles
from ..model.openings import FRAME
from ..model.parts import Group, Part
from ..spec import (BASE_TOP, CASING_W, CEILING_H, CHAIR_RAIL_H, CHAIR_RAIL_TOP, CORNICE_BOTTOM, CROWN_BOTTOM,
                    DADO_PANEL, DAMASK_BAY, DENTIL_BOTTOM, DOORCASE_TOP, HEAD_CAP_H, PANEL_MARGIN, PILASTER_W,
                    REVEAL, UPPER_PANEL, Opening, OpeningKind, Wall, openings_on, trim_extent, wall_bays)
from .cad import Canvas, Layer
from .silhouette import hidden_line, line_parts, silhouettes

DEPTH_LIMIT = {Wall.NORTH: 30.0, Wall.SOUTH: 30.0, Wall.EAST: 30.0, Wall.WEST: 92.0}
ELEVATION_GROUPS = (Group.FURNITURE, Group.SOFT_GOODS, Group.ACCESSORIES, Group.LIGHTING)
SKIP = {Wall.NORTH: ("rug", "chandelier"), Wall.SOUTH: ("rug", "chandelier"),
        Wall.EAST: ("rug", "chandelier", "drapery"), Wall.WEST: ("rug", "chandelier", "drapery")}


def profile_lines(profile: np.ndarray) -> list[float]:
    """Heights at which a horizontal molding shows an edge in elevation."""
    pts = profile[profile[:, 0] > 0.08]
    d = np.diff(pts, axis=0)
    ang = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    turn = np.abs((np.diff(ang) + 180) % 360 - 180)
    heights = [pts[0, 1], pts[-1, 1]] + list(pts[1:-1][turn > 35, 1])
    return sorted({round(float(h), 2) for h in heights})


class Elevation:
    """Wall coordinates (u along the wall, z) -> elevation drawing coordinates (left to right)."""

    def __init__(self, c: Canvas, wall: Wall):
        self.c, self.wall, self.L = c, wall, wall.value.length
        self.arch: list[shapely.Geometry] = []

    def e(self, u: float) -> float:
        return self.L - u

    def hline(self, u0: float, u1: float, z: float) -> None:
        self.arch.append(shapely.LineString([(self.e(u0), z), (self.e(u1), z)]))

    def box(self, u0: float, u1: float, z0: float, z1: float) -> None:
        self.arch.append(shapely.box(min(self.e(u0), self.e(u1)), z0, max(self.e(u0), self.e(u1)), z1).boundary)

    def vline(self, u: float, z0: float, z1: float) -> None:
        self.arch.append(shapely.LineString([(self.e(u), z0), (self.e(u), z1)]))


def _free_runs(wall: Wall, kinds: tuple[OpeningKind, ...]) -> list[tuple[float, float]]:
    cuts = [0.0]
    for o in sorted(openings_on(wall), key=lambda o: o.center_u):
        cuts.extend(trim_extent(o) if o.kind in kinds else [])
    cuts.append(wall.value.length)
    return list(zip(cuts[0::2], cuts[1::2]))


def _moldings(el: Elevation) -> None:
    every = (OpeningKind.WINDOW, OpeningKind.DOOR)
    runs = ((profiles.BASEBOARD, 0.0, (OpeningKind.DOOR,)), (profiles.CHAIR_RAIL, CHAIR_RAIL_TOP - CHAIR_RAIL_H, every),
            (profiles.CROWN, CROWN_BOTTOM, ()), (profiles.DENTIL_BACK, DENTIL_BOTTOM, ()),
            (profiles.ASTRAGAL, CORNICE_BOTTOM, ()))
    for profile, z0, kinds in runs:
        for u0, u1 in _free_runs(el.wall, kinds):
            for h in profile_lines(profile):
                el.hline(u0, u1, z0 + h)
    for u in np.arange(2.25, el.L - 1.5, 2.0):
        el.box(u - 0.5, u + 0.5, DENTIL_BOTTOM + 0.05, CROWN_BOTTOM - 0.02)


def _frame(el: Elevation, u0, u1, z0, z1, width: float) -> None:
    el.box(u0, u1, z0, z1)
    el.box(u0 + width, u1 - width, z0 + width, z1 - width)
    el.box(u0 + width * 0.35, u1 - width * 0.35, z0 + width * 0.35, z1 - width * 0.35)


def _panels(el: Elevation) -> None:
    for u0, u1 in wall_bays(el.wall):
        a, b = u0 + PANEL_MARGIN, u1 - PANEL_MARGIN
        _frame(el, a, b, *DADO_PANEL, 1.25)
        damask = (el.wall, (u0, u1)) == (Wall.WEST, DAMASK_BAY)
        upper = [] if damask else [(a, b, *UPPER_PANEL)]
        for args in upper:
            _frame(el, *args, 1.75)
    for o in openings_on(el.wall):
        e0, e1 = trim_extent(o)
        under = [(e0 + 1.0, e1 - 1.0, *DADO_PANEL)] if o.kind is OpeningKind.WINDOW else []
        for args in under:
            _frame(el, *args, 1.25)


def _window(el: Elevation, o: Opening) -> None:
    ul, ur = o.u0 - REVEAL, o.u1 + REVEAL
    ol, orr = ul - CASING_W, ur + CASING_W
    head = o.top + REVEAL
    el.box(ol, orr, CHAIR_RAIL_TOP, head + CASING_W)
    el.box(ul, ur, CHAIR_RAIL_TOP, head)
    el.box(ol + 1.15, orr - 1.15, CHAIR_RAIL_TOP, head + CASING_W - 1.15)
    el.box(ol - 1.0, orr + 1.0, head + CASING_W, head + CASING_W + HEAD_CAP_H)
    el.hline(ol - 0.6, orr + 0.6, head + CASING_W + 0.45)
    el.box(ol - 0.75, orr + 0.75, CHAIR_RAIL_TOP - 1.0, CHAIR_RAIL_TOP)
    el.box(ol + 0.5, orr - 0.5, CHAIR_RAIL_TOP - 1.0 - CASING_W, CHAIR_RAIL_TOP - 1.0)
    iu0, iu1, iz0, iz1 = o.u0 + FRAME, o.u1 - FRAME, o.bottom + FRAME, o.top - FRAME
    meet = (iz0 + iz1) / 2
    for z0, z1, bottom_rail, top_rail in ((iz0, meet + 0.6, 2.75, 1.25), (meet - 0.6, iz1, 1.25, 2.0)):
        el.box(iu0, iu1, z0, z1)
        gu0, gu1, gz0, gz1 = iu0 + 2.0, iu1 - 2.0, z0 + bottom_rail, z1 - top_rail
        el.box(gu0, gu1, gz0, gz1)
        for k in (1, 2):
            uc = gu0 + (gu1 - gu0) * k / 3
            el.vline(uc - 0.375, gz0, gz1)
            el.vline(uc + 0.375, gz0, gz1)
        zc = (gz0 + gz1) / 2
        el.hline(gu0, gu1, zc - 0.375)
        el.hline(gu0, gu1, zc + 0.375)


def _door(el: Elevation, o: Opening) -> None:
    left = (o.u0 - REVEAL - PILASTER_W, o.u0 - REVEAL)
    right = (o.u1 + REVEAL, o.u1 + REVEAL + PILASTER_W)
    for a, b in (left, right):
        el.box(a - 0.25, b + 0.25, 0.0, 7.5)
        el.box(a - 0.5, b + 0.5, 7.5, 9.25)
        el.box(a, b, 9.25, 77.0)
        for k in range(5):
            uc = b - 0.55 - (b - a - 1.1) / 5 * (k + 0.5)
            el.box(uc - 0.3, uc + 0.3, 10.5, 75.75)
        el.box(a - 0.6, b + 0.6, 77.0, 79.75)
    ea, eb = left[0] - 0.25, right[1] + 0.25
    el.box(ea, eb, 79.75, 82.25)
    el.box(ea + 0.25, eb - 0.25, 82.25, 85.0)
    el.box(ea - 2.6, eb + 2.6, 85.0, DOORCASE_TOP)
    el.hline(ea - 0.6, eb + 0.6, 85.75)
    for uc in ((left[0] + left[1]) / 2, (o.u0 + o.u1) / 2, (right[0] + right[1]) / 2):
        el.arch.append(shapely.Point(el.e(uc), 83.6).buffer(1.4).boundary)
    u0, u1, z1 = o.u0 + 0.125, o.u1 - 0.125, o.top - 0.125
    el.box(u0, u1, 0.5, z1)
    mid = 4.5
    cols = [(u0 + 4.75, (u0 + u1 - mid) / 2), ((u0 + u1 + mid) / 2, u1 - 4.75)]
    rows = [(9.5, 30.5), (38.0, 60.0), (64.5, z1 - 4.75)]
    for a, b in cols:
        for z0, zz1 in rows:
            el.box(a, b, z0, zz1)
            el.box(a + 1.6, b - 1.6, z0 + 1.6, zz1 - 1.6)
    el.arch.append(shapely.Point(el.e(o.u1 - 2.75), 36.0).buffer(1.25).boundary)


def _damask(el: Elevation) -> shapely.Polygon:
    u0, u1, z0, z1 = DAMASK_BAY[0] + 3.0, DAMASK_BAY[1] - 3.0, CHAIR_RAIL_TOP + 2.0, 79.0
    el.box(u0, u1, z0, z1)
    el.box(u0 - 1.3, u1 + 1.3, z0 - 1.3, z1)
    return shapely.box(el.e(u1), z0, el.e(u0), z1)


def _projection(wall: Wall):
    side = wall.value
    start, along, inward = np.array([*side.start, 0.0]), np.array([*side.direction, 0.0]), np.array([*side.inward, 0.0])

    def project(tris: np.ndarray):
        rel = tris - start
        u = rel @ along
        return np.stack([side.length - u, tris[..., 2]], axis=-1), rel @ inward

    return project


def _furniture(el: Elevation, parts: list[Part]) -> shapely.Geometry:
    side = el.wall.value
    start, inward = np.array([*side.start, 0.0]), np.array([*side.inward, 0.0])
    meshes = [p.mesh for p in parts if p.group in ELEVATION_GROUPS and not p.name.startswith(SKIP[el.wall])]
    near_wall = lambda tris: float(((tris.reshape(-1, 3) - start) @ inward).min()) < DEPTH_LIMIT[el.wall]
    sils = silhouettes(meshes, _projection(el.wall), near_wall)
    visible, covered = hidden_line(sils)
    for geom in visible:
        el.c.lines(line_parts(geom), Layer.ELEV_FURN)
    return covered


def _envelope(el: Elevation) -> None:
    c, L, t = el.c, el.L, 6.0
    c.rect(0, 0, L, CEILING_H, Layer.ELEV)
    for loop in ([(-t, -t), (L + t, -t), (L + t, 0), (-t, 0)],
                 [(-t, CEILING_H), (L + t, CEILING_H), (L + t, CEILING_H + t), (-t, CEILING_H + t)],
                 [(-t, 0), (0, 0), (0, CEILING_H), (-t, CEILING_H)],
                 [(L, 0), (L + t, 0), (L + t, CEILING_H), (L, CEILING_H)]):
        c.solid([loop], Layer.WALL_PATT, 252)
        c.poly(loop, Layer.ELEV, closed=True)


def _annotate(el: Elevation, title: str, number: str, scale_label: str) -> None:
    c, L = el.c, el.L
    c.dim((0, 0), (L, 0), -0.85, vertical=False)
    stops = sorted({0.0, L, *[x for o in openings_on(el.wall) for x in (el.e(o.u0), el.e(o.u1))]})
    for a, b in zip(stops[:-1], stops[1:]):
        c.dim((a, CEILING_H), (b, CEILING_H), 0.5, vertical=False)
    heights = [0.0, CEILING_H] + ([o.bottom for o in openings_on(el.wall)][:1] +
                                   [o.top for o in openings_on(el.wall)][:1] or [CHAIR_RAIL_TOP])
    levels = sorted(set(heights))
    for a, b in zip(levels[:-1], levels[1:]):
        c.dim((L, a), (L, b), 0.45, vertical=True)
    c.dim((L, 0), (L, CEILING_H), 0.85, vertical=True)
    c.circle_tag(number, (0.2 * c.scale, -1.25 * c.scale), 0.17, Layer.SYMB)
    c.text(title, (0.45 * c.scale, -1.18 * c.scale), 0.13, Layer.TEXT, TA.LEFT)
    c.text(f"SCALE: {scale_label}", (0.45 * c.scale, -1.38 * c.scale), 0.075, Layer.TEXT, TA.LEFT)
    c.text("P-1", (0.5 * c.scale, 60.0), 0.08, Layer.SYMB, TA.MIDDLE_CENTER)
    c.text("P-2", (0.5 * c.scale, 16.0), 0.08, Layer.SYMB, TA.MIDDLE_CENTER)


def elevation(c: Canvas, wall: Wall, parts: list[Part], title: str, number: str, scale_label: str) -> None:
    el = Elevation(c, wall)
    _envelope(el)
    _moldings(el)
    _panels(el)
    for o in openings_on(wall):
        (_window if o.kind is OpeningKind.WINDOW else _door)(el, o)
    damask = [_damask(el)] if wall is Wall.WEST else []
    covered = _furniture(el, parts)
    for geom in el.arch:
        c.lines(line_parts(geom.difference(covered)), Layer.ELEV_FINE)
    for region in damask:
        visible = region.difference(covered)
        for poly in shapely.get_parts(visible):
            c.pattern([np.asarray(poly.exterior.coords)] + [np.asarray(r.coords) for r in poly.interiors],
                      Layer.ELEV_PATT, "CROSS", 2.5, 45.0)
    for o in openings_on(wall):
        c.polygon_tag(o.tag, (el.e(o.center_u), -6.0 - 0.22 * c.scale), 0.12,
                      6 if o.kind is OpeningKind.WINDOW else 4, Layer.SYMB)
    _annotate(el, title, number, scale_label)
