"""Adam-style ceiling: panel molding, Greek-key border, corner fans, ring and medallion."""

import numpy as np

from ..geom.mesh import merge
from ..geom.prims import arc, lathe, sweep, tube
from ..spec import CEILING_H, CEILING_PANEL_INSET, CEILING_RING_R, CORNER_FAN_R, MEDALLION_R, ROOM_L, ROOM_W
from . import profiles
from .parts import Group, Mat, Part, Shading

DOWN = (0, 0, -1)
CX, CY = ROOM_L / 2, ROOM_W / 2
KEY_HOOK = np.array([(0, 0), (0, 4), (3, 4), (3, 1), (1, 1), (1, 3), (2, 3)], dtype=float)
KEY_UNIT = 1.1
KEY_STRIP = np.array([(-0.2, 0.0), (0.2, 0.0), (0.2, 0.16), (-0.2, 0.16)])
KEY_INSET = 7.6  # distance of the key band's outer edge from the walls


def _cw_rect(x0, y0, x1, y1, z) -> np.ndarray:
    """Clockwise from above, so a downward-facing sweep puts its profile inside."""
    return np.array([[x0, y0, z], [x0, y1, z], [x1, y1, z], [x1, y0, z]], dtype=float)


def _cw_circle(cx, cy, r, z, count) -> np.ndarray:
    return arc((cx, cy, z), r, 360.0, 0.0, count + 1)[:-1]


def greek_key_paths() -> list[np.ndarray]:
    """Plan polylines (x, y) of the running key: hooks plus a fillet line either side."""
    paths = []
    band = 4 * KEY_UNIT
    sides = [  # (origin, along, across) with 'across' pointing toward the room centre
        (np.array([KEY_INSET, KEY_INSET]), np.array([1.0, 0.0]), np.array([0.0, 1.0]), ROOM_L),
        (np.array([ROOM_L - KEY_INSET, KEY_INSET]), np.array([0.0, 1.0]), np.array([-1.0, 0.0]), ROOM_W),
        (np.array([ROOM_L - KEY_INSET, ROOM_W - KEY_INSET]), np.array([-1.0, 0.0]), np.array([0.0, -1.0]), ROOM_L),
        (np.array([KEY_INSET, ROOM_W - KEY_INSET]), np.array([0.0, -1.0]), np.array([1.0, 0.0]), ROOM_W),
    ]
    for origin, along, across, length in sides:
        run = length - 2 * KEY_INSET - 2 * (band + 1.5)
        periods = int(run // (4 * KEY_UNIT))
        start = band + 1.5 + (run - periods * 4 * KEY_UNIT) / 2
        for k in range(periods):
            local = KEY_HOOK * KEY_UNIT + [start + 4 * KEY_UNIT * k, 0.0]
            paths.append(origin + local[:, :1] * along + local[:, 1:] * across)
        for edge in (-KEY_UNIT, band + KEY_UNIT):
            a = origin + (band + 1.5) * along + edge * across
            b = origin + (length - 2 * KEY_INSET - band - 1.5) * along + edge * across
            paths.append(np.array([a, b]))
    return paths


def key_corner_points() -> list[tuple[float, float]]:
    c = KEY_INSET + 2.2
    return [(c, c), (ROOM_L - c, c), (ROOM_L - c, ROOM_W - c), (c, ROOM_W - c)]


def _greek_key() -> list:
    return [sweep(KEY_STRIP, np.c_[p, np.full(len(p), CEILING_H)], DOWN, closed=False) for p in greek_key_paths()]


def fan_corners() -> list[tuple[float, float, float]]:
    """(x, y, start angle) of the four quarter fans inside the ceiling panel."""
    inset = CEILING_PANEL_INSET + 2.6
    return [(inset, inset, 0.0), (ROOM_L - inset, inset, 90.0), (ROOM_L - inset, ROOM_W - inset, 180.0),
            (inset, ROOM_W - inset, 270.0)]


FAN_RAY_ANGLES = np.linspace(7.5, 82.5, 6)
FAN_RAY_SPAN = (3.2, CORNER_FAN_R - 1.2)
FAN_ARC_RADII = (2.6, CORNER_FAN_R)


def _rosette(x: float, y: float, radius: float, petals: int):
    prof = [(0.05, CEILING_H), (radius, CEILING_H), (radius, CEILING_H - 0.15), (radius * 0.75, CEILING_H - 0.4),
            (radius * 0.35, CEILING_H - 0.55), (0.05, CEILING_H - 0.6)]
    petal = lambda th, z: 1.0 - 0.22 * np.abs(np.sin(petals * th / 2)) ** 1.5
    return lathe(prof, 48, petal).moved((x, y, 0.0))


def _medallion():
    r = MEDALLION_R
    prof = [(0.1, CEILING_H - 0.02), (r, CEILING_H - 0.02), (r, CEILING_H - 0.35), (r - 0.6, CEILING_H - 0.5),
            (r - 0.9, CEILING_H - 0.42), (r - 1.4, CEILING_H - 0.8), (r - 3.0, CEILING_H - 1.25),
            (r - 4.6, CEILING_H - 1.55), (r - 5.4, CEILING_H - 1.35), (r - 6.0, CEILING_H - 1.8),
            (r - 7.4, CEILING_H - 2.3), (r - 8.6, CEILING_H - 2.5), (0.1, CEILING_H - 2.55)]

    def acanthus(theta, z):
        depth = np.clip((CEILING_H - 0.5 - z) / 1.2, 0.0, 1.0) * np.clip((z - (CEILING_H - 2.0)) / 0.3, 0.0, 1.0)
        return 1.0 - 0.09 * depth * np.abs(np.sin(8 * theta)) ** 0.7

    return lathe(prof, 128, acanthus).moved((CX, CY, 0.0))


def _corner_fans() -> list:
    pieces = []
    for x, y, a0 in fan_corners():
        for a in np.radians(a0 + FAN_RAY_ANGLES):
            ray = np.array([[x + r * np.cos(a), y + r * np.sin(a), CEILING_H - 0.12]
                            for r in np.linspace(*FAN_RAY_SPAN, 12)])
            pieces.append(tube(ray, np.linspace(0.18, 0.42, 12), 10))
        for radius in FAN_ARC_RADII:
            pieces.append(tube(arc((x, y, CEILING_H - 0.12), radius, a0, a0 + 90, 24), 0.28, 10))
    return pieces


def ceiling_parts() -> list[Part]:
    i = CEILING_PANEL_INSET
    panel = sweep(profiles.CEILING_PANEL, _cw_rect(i, i, ROOM_L - i, ROOM_W - i, CEILING_H), DOWN, closed=True)
    ring = sweep(profiles.CEILING_PANEL, _cw_circle(CX, CY, CEILING_RING_R, CEILING_H, 160), DOWN, closed=True)
    loop = _cw_circle(CX, CY, CEILING_RING_R - 4.0, CEILING_H - 0.1, 140)
    bead = tube(np.vstack([loop, loop[:2]]), 0.3, 10)
    rosettes = [_rosette(x, y, 2.1, 8) for x, y in key_corner_points()]
    return [
        Part("ceiling_moldings", merge([panel, ring] + _corner_fans()), Mat.TRIM_IVORY, Group.CEILING,
             Shading.CRISP),
        Part("ceiling_medallion", _medallion(), Mat.TRIM_IVORY, Group.CEILING, Shading.CRISP),
        Part("ceiling_gilt", merge(_greek_key() + rosettes + [bead]), Mat.GILT, Group.CEILING, Shading.CRISP),
    ]
