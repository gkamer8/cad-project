"""A-101 floor plan and A-102 reflected ceiling / lighting & power plan."""

import numpy as np
import shapely
from ezdxf.enums import TextEntityAlignment as TA

from ..model.ceiling import (FAN_ARC_RADII, FAN_RAY_ANGLES, FAN_RAY_SPAN, KEY_UNIT, fan_corners,
                             greek_key_paths, key_corner_points)
from ..model.drapery import window_panels
from ..model.parts import Group, Part
from ..model.profiles import CEILING_PANEL
from ..spec import (CASING_W, CEILING_PANEL_INSET, CEILING_RING_R, FURNITURE, MEDALLION_R, OPENINGS,
                    PILASTER_PROJ, PILASTER_W, REVEAL, ROOM_L, ROOM_W, RUG, SCONCE, CHANDELIER, OpeningKind,
                    Wall)
from .cad import Canvas, Layer
from .silhouette import hidden_line, line_parts, silhouettes

CUT_HEIGHT = 48.0
PLAN_GROUPS = (Group.FURNITURE, Group.SOFT_GOODS, Group.ACCESSORIES, Group.LIGHTING)
NOT_IN_PLAN = ("chandelier", "sconce", "drapery", "canopy")
CX, CY = ROOM_L / 2, ROOM_W / 2


def _thick(wall: Wall) -> float:
    return wall.value.thickness


def wall_mass(with_openings: bool) -> shapely.Polygon:
    outer = shapely.box(-_thick(Wall.WEST), -_thick(Wall.SOUTH), ROOM_L + _thick(Wall.EAST), ROOM_W + _thick(Wall.NORTH))
    ring = outer.difference(shapely.box(0, 0, ROOM_L, ROOM_W))
    gaps = [shapely.MultiPoint([o.wall.value.to_world(o.u0, 0, 0)[:2],
                                o.wall.value.to_world(o.u1, -o.wall.value.thickness, 0)[:2]]).envelope
            for o in OPENINGS]
    return ring.difference(shapely.union_all(gaps)) if with_openings else ring


def draw_walls(c: Canvas, with_openings: bool) -> None:
    for poly in shapely.get_parts(wall_mass(with_openings)):
        loops = [np.asarray(poly.exterior.coords)] + [np.asarray(r.coords) for r in poly.interiors]
        c.solid(loops, Layer.WALL_PATT, 252)
        for loop in loops:
            c.poly(loop, Layer.WALL, closed=True)


def _wall_pts(wall: Wall, pts) -> list:
    return [wall.value.to_world(u, d, 0.0)[:2] for u, d in pts]


def draw_openings(c: Canvas) -> None:
    for i, o in enumerate([o for o in OPENINGS if o.kind is OpeningKind.WINDOW]):
        w, t = o.wall, _thick(o.wall)
        for depth in (-1.85, -3.25):
            c.poly(_wall_pts(w, [(o.u0, depth), (o.u1, depth)]), Layer.GLAZ, closed=False)
        c.poly(_wall_pts(w, [(o.u0, -t + 0.75), (o.u1, -t + 0.75)]), Layer.GLAZ, closed=False)
        ol, orr = o.u0 - REVEAL - CASING_W - 0.75, o.u1 + REVEAL + CASING_W + 0.75
        c.poly(_wall_pts(w, [(ol, 0), (ol, 1.9), (orr, 1.9), (orr, 0)]), Layer.MILL, closed=False)
        for panel in window_panels(i, o.u0, o.u1):
            s = np.linspace(0, 1, 60)
            u = panel.span_top[0] + (panel.span_top[1] - panel.span_top[0]) * s
            d = panel.depth[0] + 1.1 * np.sin(2 * np.pi * panel.folds * s)
            c.poly(_wall_pts(w, zip(u, d)), Layer.SOFT, closed=False)
        c.poly(_wall_pts(w, [(ol - 13.0, 3.6), (orr + 13.0, 3.6)]), Layer.FURN_OVHD, closed=False)
    door = [o for o in OPENINGS if o.kind is OpeningKind.DOOR][0]
    w = door.wall
    hinge = w.value.to_world(door.u0, 0, 0)[:2]
    c.poly(_wall_pts(w, [(door.u0, 0), (door.u0, door.width), (door.u0 + 1.75, door.width),
                         (door.u0 + 1.75, 0)]), Layer.DOOR, closed=True)
    c.arc(hinge, door.width, 90.0, 180.0, Layer.DOOR)
    c.poly(_wall_pts(w, [(door.u0, -0.75), (door.u1, -0.75)]), Layer.DOOR, closed=False)
    for a, b in ((door.u0 - REVEAL - PILASTER_W, door.u0 - REVEAL), (door.u1 + REVEAL, door.u1 + REVEAL + PILASTER_W)):
        c.poly(_wall_pts(w, [(a - 0.25, 0), (a - 0.25, PILASTER_PROJ + 0.5), (b + 0.25, PILASTER_PROJ + 0.5),
                             (b + 0.25, 0)]), Layer.MILL, closed=False)


def _plan_projection(tris: np.ndarray):
    return tris[..., :2], tris[..., 2]


def draw_furniture(c: Canvas, parts: list[Part]) -> shapely.Geometry:
    meshes = [p.mesh for p in parts if p.group in PLAN_GROUPS and not p.name.startswith(NOT_IN_PLAN)]
    sils = silhouettes(meshes, _plan_projection, lambda tris: tris[..., 2].min() < CUT_HEIGHT)
    visible, covered = hidden_line(sils)
    for geom in visible:
        c.lines(line_parts(geom), Layer.FURN)
    canopy = [p.mesh for p in parts if p.name.startswith("canopy")]
    over = shapely.union_all([s.shape for s in silhouettes(canopy, _plan_projection, lambda t: True)])
    c.lines(line_parts(over.boundary), Layer.FURN_OVHD)
    raised = shapely.union_all([s.shape for s in sils if s.near > 1.0])
    rug = RUG.placements[0]
    inset = 11.0
    border = shapely.box(rug.x - RUG.size[1] / 2 + inset, rug.y - RUG.size[0] / 2 + inset,
                         rug.x + RUG.size[1] / 2 - inset, rug.y + RUG.size[0] / 2 - inset)
    c.lines(line_parts(border.boundary.difference(raised)), Layer.SOFT)
    return covered


def draw_floor_pattern(c: Canvas, covered) -> None:
    door = [o for o in OPENINGS if o.kind is OpeningKind.DOOR][0]
    swing = shapely.Point(door.wall.value.to_world(door.u0, 0, 0)[:2]).buffer(door.width)
    free = shapely.box(0, 0, ROOM_L, ROOM_W).difference(covered.buffer(0.5)).difference(swing)
    for poly in shapely.get_parts(free):
        loops = [np.asarray(poly.exterior.coords)] + [np.asarray(r.coords) for r in poly.interiors]
        c.pattern(loops, Layer.FLOR_PATT, "AR-HBONE", 0.35, 45.0)


def _dimension_strings(c: Canvas) -> None:
    ts, tn, tw, te = _thick(Wall.SOUTH), _thick(Wall.NORTH), _thick(Wall.WEST), _thick(Wall.EAST)
    xs = [0.0] + sorted(o.wall.value.to_world(o.center_u, 0, 0)[0] for o in OPENINGS if o.wall is Wall.SOUTH) + [ROOM_L]
    for a, b in zip(xs[:-1], xs[1:]):
        c.dim((a, -ts), (b, -ts), -0.55, vertical=False)
        c.dim((a, ROOM_W + tn), (b, ROOM_W + tn), 0.55, vertical=False)
    c.dim((0, -ts), (ROOM_L, -ts), -0.95, vertical=False)
    c.dim((0, ROOM_W + tn), (ROOM_L, ROOM_W + tn), 0.95, vertical=False)
    c.dim((-tw, 0), (-tw, ROOM_W), -0.6, vertical=True)
    door_y = Wall.EAST.value.to_world(72.0, 0, 0)[1]
    for a, b in ((0.0, door_y), (door_y, ROOM_W)):
        c.dim((ROOM_L + te, a), (ROOM_L + te, b), 0.55, vertical=True)
    c.dim((ROOM_L + te, 0), (ROOM_L + te, ROOM_W), 0.95, vertical=True)


def _tags(c: Canvas) -> None:
    for o in OPENINGS:
        side = o.wall.value
        at = side.to_world(o.center_u, -side.thickness - 0.32 * c.scale, 0)[:2]
        sides = 6 if o.kind is OpeningKind.WINDOW else 4
        c.polygon_tag(o.tag, at, 0.13, sides, Layer.SYMB)
    offsets = {"F-1": (14.0, 0.0), "F-2": (27.0, 48.0), "F-3": (14.0, 0.0), "F-4": (0.0, 31.0),
               "F-5": (-20.0, 0.0), "F-6": (-6.0, 15.0), "R-1": (40.0, -36.0)}
    for item in FURNITURE:
        for place in item.placements:
            dx, dy = offsets[item.tag]
            dy = dy if place.y <= CY else -dy
            c.circle_tag(item.tag, (place.x + dx, place.y + dy), 0.12, Layer.SYMB)


def elevation_marker(c: Canvas, at, sheet_refs: dict[Wall, str]) -> None:
    r = 0.2 * c.scale
    c.circle(at, r, Layer.SYMB)
    pointers = {Wall.NORTH: (0, 1), Wall.SOUTH: (0, -1), Wall.EAST: (1, 0), Wall.WEST: (-1, 0)}
    for wall, (dx, dy) in pointers.items():
        tip = (at[0] + dx * r * 1.6, at[1] + dy * r * 1.6)
        side = (-dy * r * 0.7, dx * r * 0.7)
        base = (at[0] + dx * r * 0.7, at[1] + dy * r * 0.7)
        c.solid([[tip, (base[0] + side[0], base[1] + side[1]), (base[0] - side[0], base[1] - side[1])]],
                Layer.SYMB, 250)
        lab = (at[0] + dx * r * 2.45, at[1] + dy * r * 2.15)
        c.text(sheet_refs[wall], lab, 0.06, Layer.SYMB, TA.MIDDLE_CENTER)


def floor_plan(c: Canvas, parts: list[Part], sheet_refs: dict[Wall, str]) -> None:
    draw_walls(c, with_openings=True)
    draw_openings(c)
    covered = draw_furniture(c, parts)
    draw_floor_pattern(c, covered)
    _dimension_strings(c)
    _tags(c)
    c.text("PRIMARY BEDROOM", (150.0, 100.0), 0.13, Layer.TEXT, TA.MIDDLE_CENTER)
    c.text("192 SF  |  CLG 8'-0\"", (150.0, 94.0), 0.08, Layer.TEXT, TA.MIDDLE_CENTER)
    elevation_marker(c, (150.0, 50.0), sheet_refs)


# ------------------------------------------------------------------ reflected ceiling plan
SWITCHES = (("S3D", Wall.EAST, 101.5), ("SD", Wall.EAST, 106.0), ("S", Wall.EAST, 110.5), ("S3D", Wall.WEST, 2.0))
RECEPTACLES = ((Wall.WEST, 4.0), (Wall.WEST, 140.0), (Wall.SOUTH, 40.0), (Wall.SOUTH, 152.0),
               (Wall.NORTH, 40.0), (Wall.NORTH, 152.0))
SWITCHED = ((Wall.EAST, 8.0), (Wall.EAST, 136.0))  # commode lamps, on the "S" switch
CIRCUITS = (((Wall.EAST, 101.5), CHANDELIER), ((Wall.WEST, 2.0), CHANDELIER), ((Wall.EAST, 106.0), SCONCE))


def _ceiling_ornament(c: Canvas) -> None:
    for inset, layer in ((4.5, Layer.CLNG), (1.4, Layer.CLNG_ORNM), (0.4, Layer.CLNG_ORNM)):
        c.rect(inset, inset, ROOM_L - inset, ROOM_W - inset, layer)
    width = CEILING_PANEL[:, 0].max()
    for inset in (CEILING_PANEL_INSET, CEILING_PANEL_INSET + width):
        c.rect(inset, inset, ROOM_L - inset, ROOM_W - inset, Layer.CLNG)
    for r in (CEILING_RING_R, CEILING_RING_R - width, CEILING_RING_R - 4.0, MEDALLION_R, MEDALLION_R - 3.5, 3.0):
        c.circle((CX, CY), r, Layer.CLNG_ORNM)
    for path in greek_key_paths():
        c.poly(path, Layer.CLNG_ORNM, closed=False)
    for at in key_corner_points():
        c.circle(at, KEY_UNIT * 1.9, Layer.CLNG_ORNM)
    for x, y, a0 in fan_corners():
        for a in np.radians(a0 + FAN_RAY_ANGLES):
            c.line((x + FAN_RAY_SPAN[0] * np.cos(a), y + FAN_RAY_SPAN[0] * np.sin(a)),
                   (x + FAN_RAY_SPAN[1] * np.cos(a), y + FAN_RAY_SPAN[1] * np.sin(a)), Layer.CLNG_ORNM)
        for r in FAN_ARC_RADII:
            c.arc((x, y), r, a0, a0 + 90.0, Layer.CLNG_ORNM)


def _fixtures(c: Canvas) -> None:
    ch = CHANDELIER.placements[0]
    c.circle((ch.x, ch.y), CHANDELIER.size[0] / 2, Layer.LITE)
    c.circle((ch.x, ch.y), 6.0, Layer.LITE)
    for a in np.linspace(0, 2 * np.pi, 6, endpoint=False):
        c.circle((ch.x + 10.4 * np.cos(a), ch.y + 10.4 * np.sin(a)), 1.0, Layer.LITE)
    c.circle_tag("L-1", (ch.x + 20.0, ch.y + 14.0), 0.12, Layer.SYMB)
    for place in SCONCE.placements:
        inward = np.array([-np.sin(np.radians(place.rotation)), np.cos(np.radians(place.rotation))])
        c.arc((place.x, place.y), 4.0, place.rotation, place.rotation + 180.0, Layer.LITE)
        c.line((place.x - 4.0, place.y), (place.x + 4.0, place.y), Layer.LITE)
        c.circle_tag("L-2", np.array([place.x + 12.0, place.y]) + inward * 10.0, 0.12, Layer.SYMB)


def _on_wall(wall: Wall, u: float, depth: float) -> np.ndarray:
    return wall.value.to_world(u, depth, 0.0)[:2]


def _power(c: Canvas) -> None:
    r = 0.07 * c.scale
    for wall, u in RECEPTACLES + SWITCHED:
        inward, along = wall.value.inward, np.asarray(wall.value.direction)
        center = _on_wall(wall, u, r * 1.6)
        c.circle(center, r, Layer.POWR)
        for k in (-1, 1):
            c.line(center + along * r * 0.55 * k - inward * r * 1.5, center + along * r * 0.55 * k + inward * r,
                   Layer.POWR)
    for wall, u in SWITCHED:
        c.solid([[_on_wall(wall, u - r, r * 2.6), _on_wall(wall, u, r * 3.6), _on_wall(wall, u + r, r * 2.6)]],
                Layer.POWR, 250)
    for label, wall, u in SWITCHES:
        c.text(label, _on_wall(wall, u, 0.2 * c.scale), 0.07, Layer.POWR, TA.MIDDLE_CENTER)
    ch = CHANDELIER.placements[0]
    targets = {CHANDELIER: [np.array([ch.x, ch.y])],
               SCONCE: [np.array([p.x, p.y]) + 5.0 * np.array([0.0, 1.0 if p.y < CY else -1.0])
                           for p in SCONCE.placements]}
    for (wall, u), fixture in CIRCUITS:
        start = _on_wall(wall, u, 0.42 * c.scale)
        for end in targets[fixture]:
            mid = (start + end) / 2 + np.array([-(end - start)[1], (end - start)[0]]) * 0.15
            c.poly([start, mid, end], Layer.CIRC, closed=False)


def ceiling_plan(c: Canvas) -> None:
    draw_walls(c, with_openings=False)
    _ceiling_ornament(c)
    _fixtures(c)
    _power(c)
    c.text("PAINTED PLASTER CEILING P-3  |  8'-0\" AFF", (CX, CY - 40.0), 0.085, Layer.TEXT, TA.MIDDLE_CENTER)
    c.text("GILT GREEK-KEY BORDER GL-1", (CX, 21.0), 0.075, Layer.TEXT, TA.MIDDLE_CENTER)
