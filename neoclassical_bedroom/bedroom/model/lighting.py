"""L-1 chandelier, L-2 sconces, L-3 bedside lamps, L-4 bouillotte lamps (+ their light sources)."""

import numpy as np

from ..geom.mesh import Mesh
from ..geom.prims import smooth_turning, superellipsoid, sweep, tube
from ..spec import BEDSIDE_LAMP, BOUILLOTTE, CHANDELIER, SCONCE, Placement
from .kit import bead, bow, part_at, revolve_open, ring, turned, wreath
from .parts import CANDLE_2200K, WARM_2700K, Group, Lamp, Mat, Part, Shading

FLAME = [(0.05, 0.0), (0.3, 0.15), (0.42, 0.55), (0.34, 1.0), (0.16, 1.35), (0.04, 1.55)]
CUP = [(0.05, 0.0), (0.35, 0.0), (0.35, 0.3), (1.05, 0.45), (1.25, 0.62), (0.7, 0.62), (0.62, 0.8), (0.05, 0.82)]


def _candle(at: np.ndarray, sleeve: float) -> dict[Mat, list[Mesh]]:
    x, y, z = at
    return {
        Mat.GILT: [turned(CUP, 24).moved((x, y, z))],
        Mat.WAX: [turned([(0.05, 0.0), (0.52, 0.0), (0.52, sleeve), (0.3, sleeve + 0.1), (0.05, sleeve + 0.12)], 20)
                  .moved((x, y, z + 0.8))],
        Mat.BULB: [turned(FLAME, 16).moved((x, y, z + 0.8 + sleeve + 0.05))],
    }


def _flame_point(at: np.ndarray, sleeve: float) -> tuple[float, float, float]:
    return (float(at[0]), float(at[1]), float(at[2] + 0.8 + sleeve + 0.7))


def _merge_into(out: dict[Mat, list[Mesh]], extra: dict[Mat, list[Mesh]]) -> None:
    for mat, meshes in extra.items():
        out[mat] = out[mat] + meshes


def _strand(points: np.ndarray, spacing: float) -> list[Mesh]:
    seg = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    s = np.arange(spacing / 2, seg[-1], spacing)
    centers = np.c_[[np.interp(s, seg, points[:, k]) for k in range(3)]].T
    return [bead(0.24).moved(c) for c in centers]


def _chandelier() -> tuple[dict[Mat, list[Mesh]], list[tuple[float, float, float]]]:
    out = {Mat.GILT: [], Mat.CRYSTAL: [], Mat.WAX: [], Mat.BULB: []}
    out[Mat.GILT].append(turned([(0.1, 0.0), (3.0, 0.0), (3.0, -0.35), (2.4, -1.2), (1.0, -2.0), (0.4, -2.2),
                                 (0.1, -2.25)][::-1], 32))
    out[Mat.GILT].append(tube(np.array([[0, 0, -2.2], [0, 0, -5.4]]), 0.3, 12))
    out[Mat.GILT].append(superellipsoid((1.3, 1.3, 1.5), 1, 1, 8, 12).moved((0, 0, -3.6)))
    top_r, top_z, mid_r, mid_z = 6.0, -5.2, 10.4, -11.0
    out[Mat.GILT].append(ring(top_r, top_z, 0.28))
    for t in np.linspace(0, 2 * np.pi, 4, endpoint=False):
        out[Mat.GILT].append(tube(np.array([[0, 0, -5.0], [top_r * np.cos(t), top_r * np.sin(t), top_z]]), 0.12, 6))
    band = np.array([(-0.7, -0.45), (0.7, -0.45), (0.85, -0.1), (0.7, 0.45), (-0.7, 0.45)])
    circle = np.c_[mid_r * np.cos(np.linspace(0, 2 * np.pi, 96, endpoint=False)),
                   mid_r * np.sin(np.linspace(0, 2 * np.pi, 96, endpoint=False)), np.full(96, mid_z)]
    out[Mat.GILT].append(sweep(band, circle, (0, 0, 1), closed=True))
    t = np.linspace(0, 1, 24)
    for a in np.linspace(0, 2 * np.pi, 16, endpoint=False):
        r = top_r + (mid_r - top_r) * t + 0.9 * np.sin(np.pi * t)
        out[Mat.CRYSTAL] += _strand(np.c_[r * np.cos(a), r * np.sin(a), top_z + (mid_z + 0.5 - top_z) * t], 0.72)
    for a in np.linspace(0, 2 * np.pi, 24, endpoint=False) + np.pi / 24:
        r = 2.0 + (mid_r - 2.2) * np.cos(np.pi * t / 2)
        out[Mat.CRYSTAL] += _strand(np.c_[r * np.cos(a), r * np.sin(a), mid_z - 0.5 - 5.8 * np.sin(np.pi * t / 2)], 0.7)
    out[Mat.GILT].append(turned([(0.05, -18.2), (1.0, -18.0), (2.3, -17.2), (2.4, -16.9), (0.05, -16.8)], 28))
    out[Mat.CRYSTAL].append(superellipsoid((2.4, 2.4, 2.4), 1, 1, 10, 16).moved((0, 0, -19.6)))
    drop = [(0.05, -2.4), (0.42, -1.9), (0.62, -1.2), (0.5, -0.5), (0.05, 0.0)]
    for a in np.linspace(0, 2 * np.pi, 12, endpoint=False) + np.pi / 12:
        out[Mat.CRYSTAL].append(turned(drop, 8).moved((11.0 * np.cos(a), 11.0 * np.sin(a), mid_z - 0.9)))
    flames = []
    for a in np.linspace(0, 2 * np.pi, 6, endpoint=False):
        base = np.array([mid_r * np.cos(a), mid_r * np.sin(a), mid_z + 0.45])
        _merge_into(out, _candle(base, 4.0))
        flames.append(_flame_point(base, 4.0))
    return out, flames


def _sconce() -> tuple[dict[Mat, list[Mesh]], list[tuple[float, float, float]]]:
    out = {Mat.GILT: [], Mat.WAX: [], Mat.BULB: [], Mat.TOLE: []}
    out[Mat.GILT].append(superellipsoid((4.6, 0.8, 8.0), 0.5, 0.5, 12, 28).moved((0, 0.4, 0)))
    out[Mat.GILT] += [m.moved((0, 1.0, 1.6)) for m in wreath(1.5, 0.9, 10)]
    out[Mat.GILT] += [m.moved((0, 1.0, 3.8)) for m in bow(3.0)]
    flames = []
    for side in (-1, 1):
        s = np.linspace(0, 1, 24)
        arm = np.c_[side * (0.4 + 5.6 * s), 0.8 + 4.6 * s ** 0.7, -2.2 + 1.0 * s - 1.8 * np.sin(np.pi * s)]
        out[Mat.GILT].append(tube(arm, 0.28, 10))
        end = arm[-1] + np.array([0, 0, 0.1])
        _merge_into(out, _candle(end, 3.0))
        flames.append(_flame_point(end, 3.0))
        shade = revolve_open([(2.7, 0.0), (1.4, 3.6), (1.3, 3.7)], 32, smooth_turning)
        out[Mat.TOLE].append(shade.moved((end[0], end[1], end[2] + 3.6)))
        out[Mat.GILT].append(ring(2.72, 0.0, 0.1).moved((end[0], end[1], end[2] + 3.6)))
    return out, flames


def _bedside_lamp() -> tuple[dict[Mat, list[Mesh]], list[tuple[float, float, float]]]:
    out = {Mat.GILT: [], Mat.PORCELAIN: [], Mat.SHADE: [], Mat.BRASS: []}
    out[Mat.GILT].append(turned([(0.05, 0.0), (3.0, 0.0), (3.0, 0.6), (2.6, 0.8), (2.2, 1.4), (0.05, 1.45)], 4)
                         .transformed(_rot_z(45)))
    out[Mat.PORCELAIN].append(turned([(0.05, 1.4), (1.6, 1.4), (1.4, 1.9), (1.0, 2.4), (2.6, 4.5), (3.4, 6.8),
                                      (3.2, 9.0), (2.2, 10.6), (1.2, 11.4), (1.5, 12.0), (1.5, 12.4),
                                      (0.05, 12.5)], 48))
    for side in (-1, 1):
        t = np.linspace(-0.4, np.pi + 0.4, 16)
        out[Mat.GILT].append(tube(np.c_[side * (3.3 + 1.0 * np.sin(t)), np.zeros(16), 8.6 + 1.2 * np.cos(t)], 0.14, 8))
    out[Mat.GILT].append(turned([(0.05, 12.4), (1.1, 12.4), (0.6, 13.2), (0.5, 14.0), (0.05, 14.1)], 24))
    out[Mat.BRASS].append(tube(np.array([[0, 0, 14.0], [0, 0, 18.5]]), 0.22, 10))
    out[Mat.BRASS].append(turned([(0.05, 18.2), (0.75, 18.2), (0.75, 20.4), (0.05, 20.5)], 16))
    for side in (-1, 1):
        harp = np.c_[side * np.r_[np.linspace(0.6, 4.2, 8), np.linspace(4.2, 0.15, 10)], np.zeros(18),
                     np.r_[np.linspace(18.6, 20.0, 8), np.linspace(20.5, 25.6, 10)]]
        out[Mat.BRASS].append(tube(harp, 0.07, 6))
    pleats = lambda th, z: 1.0 + 0.028 * np.sign(np.sin(40 * th)) * np.abs(np.sin(40 * th)) ** 0.5
    out[Mat.SHADE].append(revolve_open([(7.0, 16.5), (4.6, 25.4)], 160, pleats))
    out[Mat.GILT] += [ring(7.05, 16.5, 0.12), ring(4.62, 25.4, 0.1)]
    out[Mat.GILT].append(turned([(0.05, 25.5), (0.45, 25.6), (0.6, 26.2), (0.3, 26.8), (0.05, 27.0)], 16))
    return out, [(0.0, 0.0, 21.2)]


def _bouillotte() -> tuple[dict[Mat, list[Mesh]], list[tuple[float, float, float]]]:
    out = {Mat.BRASS: [], Mat.TOLE: [], Mat.GILT: [], Mat.WAX: [], Mat.BULB: []}
    out[Mat.BRASS].append(turned([(0.05, 0.0), (6.0, 0.0), (6.2, 0.3), (6.0, 0.9), (5.2, 1.1), (1.2, 1.3),
                                  (0.9, 1.6), (0.05, 1.7)], 48))
    out[Mat.BRASS].append(tube(np.array([[0, 0, 1.6], [0, 0, 22.4]]), 0.42, 12))
    out[Mat.BRASS].append(turned([(0.05, 22.2), (0.7, 22.4), (0.9, 23.0), (0.5, 23.6), (0.05, 23.8)], 20))
    flames = []
    for a in np.linspace(0, 2 * np.pi, 3, endpoint=False) + np.pi / 2:
        s = np.linspace(0, 1, 16)
        arm = np.c_[(0.4 + 3.9 * s) * np.cos(a), (0.4 + 3.9 * s) * np.sin(a), 6.0 + 1.6 * s - 1.2 * np.sin(np.pi * s)]
        out[Mat.BRASS].append(tube(arm, 0.22, 8))
        _merge_into(out, _candle(arm[-1], 3.4))
        flames.append(_flame_point(arm[-1], 3.4))
    profile = [(6.2, 13.9), (5.8, 15.4), (5.2, 17.0), (5.0, 17.5), (0.6, 17.5)]
    out[Mat.TOLE].append(revolve_open(profile, 64, smooth_turning))
    out[Mat.GILT] += [ring(6.22, 13.9, 0.14), ring(5.95, 14.9, 0.08), ring(5.02, 17.45, 0.1)]
    return out, flames


def _rot_z(deg: float) -> np.ndarray:
    a = np.radians(deg)
    m = np.eye(4)
    m[:2, :2] = [[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]
    return m


SHADING = {Mat.GILT: Shading.CRISP, Mat.CRYSTAL: Shading.FLAT, Mat.WAX: Shading.SOFT, Mat.BULB: Shading.SOFT,
           Mat.TOLE: Shading.SOFT, Mat.PORCELAIN: Shading.SOFT, Mat.SHADE: Shading.SOFT, Mat.BRASS: Shading.CRISP}


def _fixture(name: str, built, placements: tuple[Placement, ...], watts: float, radius: float,
             color) -> tuple[list[Part], list[Lamp]]:
    meshes, points = built
    parts = [part_at(f"{name}_{mat.name.lower()}", m, placements, mat, Group.LIGHTING, SHADING[mat])
             for mat, m in meshes.items()]
    lamps = []
    for i, where in enumerate(placements):
        for j, p in enumerate(points):
            world = where.matrix() @ np.array([*p, 1.0])
            lamps.append(Lamp(f"{name}_{i}_{j}", tuple(world[:3]), watts, radius, color))
    return parts, lamps


def lighting() -> tuple[list[Part], list[Lamp]]:
    parts, lamps = [], []
    for spec in (("chandelier", _chandelier(), CHANDELIER.placements, 9.0, 0.35, CANDLE_2200K),
                 ("sconce", _sconce(), SCONCE.placements, 7.0, 0.35, CANDLE_2200K),
                 ("bedside_lamp", _bedside_lamp(), BEDSIDE_LAMP.placements, 30.0, 0.8, WARM_2700K),
                 ("bouillotte", _bouillotte(), BOUILLOTTE.placements, 7.0, 0.35, CANDLE_2200K)):
        p, l = _fixture(*spec)
        parts += p
        lamps += l
    return parts, lamps
