"""F-3 nightstands, F-4 bench, F-5 commodes, F-6 oval mirrors and commode garnitures."""

import numpy as np

from ..geom.mesh import Mesh
from ..geom.prims import box, lathe, prism, smooth_turning, sweep, tube
from ..spec import BENCH, COMMODE, MIRROR, NIGHTSTAND, Placement
from . import profiles
from .kit import bow, cushion, part_at, turned, turned_leg, wreath
from .parts import Group, Mat, Part, Shading

UP = (0, 0, 1)
FRONT = (0, 1, 0)


def _front_rect(x0, x1, z0, z1, y) -> np.ndarray:
    """Rectangle on a +y-facing surface, ordered so a frame sweep turns inward."""
    return np.array([[x1, y, z0], [x0, y, z0], [x0, y, z1], [x1, y, z1]], dtype=float)


def _ring_pull(x: float, y: float, z: float) -> list[Mesh]:
    rose = lathe([(0.05, 0.0), (0.7, 0.0), (0.62, 0.15), (0.3, 0.3), (0.05, 0.34)], 20, smooth_turning)
    rose = rose.transformed(_to_front()).moved((x, y, z))
    t = np.linspace(0, 2 * np.pi, 25)
    ring = tube(np.c_[x + 0.85 * np.sin(t), np.full(25, y + 0.45), z - 0.85 - 0.85 * np.cos(t)], 0.12, 8)
    return [rose, ring]


def _to_front() -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]
    return m


def _gallery(w: float, d: float, z: float) -> list[Mesh]:
    """Pierced brass gallery on three sides of a top."""
    pieces = []
    rail = np.array([[-w / 2, d / 2 - 0.6, z + 1.2], [-w / 2, -d / 2, z + 1.2], [w / 2, -d / 2, z + 1.2],
                     [w / 2, d / 2 - 0.6, z + 1.2]])
    for a, b in zip(rail[:-1], rail[1:]):
        pieces.append(tube(np.array([a, b]), 0.12, 6))
        for p in np.linspace(a, b, int(np.linalg.norm(b - a) / 1.0)):
            pieces.append(tube(np.array([[p[0], p[1], z], [p[0], p[1], z + 1.2]]), 0.05, 5))
    return pieces


def _case(w: float, d: float, leg_h: float, top_z: float, drawers: list[tuple[float, float]],
          canted: bool) -> dict[Mat, list[Mesh]]:
    """Lacquered case on turned legs with drawers, gilt mounts and a marble top."""
    out = {Mat.LACQUER: [], Mat.GILT: [], Mat.MARBLE: []}
    hx, hy = w / 2, d / 2
    body_z0 = leg_h
    out[Mat.LACQUER].append(box((-hx + 0.6, -hy + 0.4, body_z0), (hx - 0.6, hy - 0.4, top_z)))
    for x in (-hx + 1.2, hx - 1.2):
        for y in (-hy + 1.2, hy - 1.2):
            out[Mat.LACQUER].append(turned_leg(leg_h + 0.5, 0.95, 0.6).moved((x, y, 0.0)))
            out[Mat.GILT].append(turned([(0.05, -0.2), (1.12, -0.2), (1.12, 0.35), (0.05, 0.35)], 24)
                                 .moved((x, y, leg_h - 0.2)))
    for z0, z1 in drawers:
        out[Mat.LACQUER].append(box((-hx + 2.4, hy - 0.4, z0), (hx - 2.4, hy + 0.05, z1)))
        bead = profiles.scaled(profiles.BEAD, 0.8, 0.8)
        out[Mat.GILT].append(sweep(bead, _front_rect(-hx + 2.4, hx - 2.4, z0, z1, hy + 0.05), FRONT, closed=True))
        pulls = (-w * 0.24, w * 0.24) if w > 30 else (0.0,)
        for x in pulls:
            out[Mat.GILT].extend(_ring_pull(x, hy + 0.05, (z0 + z1) / 2 + 0.9))
    stile_x = hx - 1.6
    for x in (-stile_x, stile_x):
        out[Mat.GILT].append(box((x - 0.5, hy - 0.45, body_z0 + 0.6), (x + 0.5, hy - 0.2, top_z - 0.6)))
        flutes = [box((x + o - 0.08, hy - 0.2, body_z0 + 1.6), (x + o + 0.08, hy - 0.05, top_z - 1.6))
                  for o in (-0.25, 0.0, 0.25)]
        out[Mat.GILT].extend(flutes if canted else [])
    out[Mat.GILT].append(box((-hx + 0.6, hy - 0.45, top_z - 0.9), (hx - 0.6, hy - 0.15, top_z - 0.35)))
    out[Mat.MARBLE].append(box((-hx - 0.4, -hy - 0.1, top_z), (hx + 0.4, hy + 0.5, top_z + 1.2)))
    return out


def _nightstand() -> dict[Mat, list[Mesh]]:
    w, d, h = NIGHTSTAND.size
    out = _case(w, d, 13.0, h - 1.2, [(14.0, 19.2), (19.8, 25.8)], canted=False)
    out[Mat.LACQUER].append(box((-w / 2 + 1.0, -d / 2 + 1.0, 4.0), (w / 2 - 1.0, d / 2 - 1.0, 4.7)))
    out[Mat.BRASS] = _gallery(w + 0.6, d + 0.4, h)
    return out


def _commode() -> dict[Mat, list[Mesh]]:
    w, d, h = COMMODE.size
    return _case(w, d, 6.0, h - 1.2, [(6.8, 14.6), (15.2, 23.0), (23.6, 31.8)], canted=True)


def _bench() -> dict[Mat, list[Mesh]]:
    w, d, h = BENCH.size
    out = {Mat.GILT: [], Mat.VELVET: []}
    for x in (-w / 2 + 1.5, 0.0, w / 2 - 1.5):
        for y in (-d / 2 + 1.5, d / 2 - 1.5):
            out[Mat.GILT].append(turned_leg(12.6, 0.9, 0.58).moved((x, y, 0.0)))
    rail = np.array([[-w / 2, -d / 2, 12.2], [w / 2, -d / 2, 12.2], [w / 2, d / 2, 12.2], [-w / 2, d / 2, 12.2]])
    apron = profiles.scaled(profiles.CHAIR_RAIL, 0.9, 1.25)
    out[Mat.GILT].append(sweep(apron, rail[::-1], UP, closed=True))
    out[Mat.GILT].append(box((-w / 2 + 0.2, -d / 2 + 0.2, 12.2), (w / 2 - 0.2, d / 2 - 0.2, 15.6)))
    seat = cushion((w - 1.0, d - 1.0, 4.4), 0.32).moved((0, 0, 17.0))
    out[Mat.VELVET].append(seat)
    return out


def _oval(a: float, b: float, y: float, zc: float, count: int) -> np.ndarray:
    """Ellipse in the x-z plane, counter-clockwise for a viewer looking from +y."""
    t = np.linspace(0, 2 * np.pi, count, endpoint=False)
    return np.c_[-a * np.cos(t), np.full(count, y), zc + b * np.sin(t)]


def _mirror() -> dict[Mat, list[Mesh]]:
    w, _, _ = MIRROR.size
    a, b, zc = w / 2, 17.0, 17.0
    frame = sweep(profiles.scaled(profiles.GILT_FRAME, 1.15, 1.2), _oval(a, b, -1.0, zc, 120), FRONT, closed=True)
    inner = _oval(a - 2.2, b - 2.2, 0.0, zc, 96)[:, [0, 2]]
    plate = prism(inner[::-1] if _area(inner) < 0 else inner, 0.3, 0.6)
    plate = plate.transformed(_xz_plane())
    crest = [m.moved((0, -0.4, zc + b + 2.6)) for m in wreath(2.2, 1.3, 12) + [x.moved((0, 0, 3.0)) for x in bow(5.0)]]
    return {Mat.GILT: [frame] + crest, Mat.MIRROR: [plate]}


def _area(poly: np.ndarray) -> float:
    return float(np.sum(poly[:, 0] * np.roll(poly[:, 1], -1) - np.roll(poly[:, 0], -1) * poly[:, 1]))


def _xz_plane() -> np.ndarray:
    """Prism built in (x, y) with thickness along z -> stood up in the x-z plane (thickness along y)."""
    m = np.eye(4)
    m[:3, :3] = [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
    return m


def _garniture_urn() -> dict[Mat, list[Mesh]]:
    body = turned([(0.05, 0.0), (2.0, 0.0), (2.0, 0.5), (1.2, 0.8), (0.9, 1.6), (2.4, 3.6), (2.9, 5.4),
                   (2.6, 7.0), (1.6, 8.0), (1.3, 8.6), (1.9, 9.1), (1.9, 9.5), (0.05, 9.6)], 40)
    handles = [tube(np.c_[side * (2.4 + 1.1 * np.sin(t)), np.zeros(14), 6.2 + 1.6 * np.cos(t)], 0.18, 8)
               for side in (-1, 1) for t in [np.linspace(0.3, np.pi - 0.3, 14)]]
    rim = turned([(1.55, 8.85), (2.0, 8.85), (2.0, 9.25), (1.55, 9.25)], 32)
    return {Mat.LACQUER: [body], Mat.GILT: handles + [rim]}


def _parts(name: str, meshes: dict[Mat, list[Mesh]], placements, group: Group) -> list[Part]:
    shading = {Mat.LACQUER: Shading.EASED, Mat.GILT: Shading.CRISP, Mat.MARBLE: Shading.EASED,
               Mat.BRASS: Shading.CRISP, Mat.VELVET: Shading.SOFT, Mat.MIRROR: Shading.FLAT}
    return [part_at(f"{name}_{mat.name.lower()}", m, placements, mat, group, shading[mat])
            for mat, m in meshes.items()]


def urn_placements() -> tuple[Placement, ...]:
    return tuple(Placement(c.x, c.y + (-9.0 if c.y < 72 else 9.0), c.z + COMMODE.size[2], c.rotation)
                 for c in COMMODE.placements)


def casegood_parts() -> list[Part]:
    return [
        *_parts("nightstand", _nightstand(), NIGHTSTAND.placements, Group.FURNITURE),
        *_parts("commode", _commode(), COMMODE.placements, Group.FURNITURE),
        *_parts("bench", _bench(), BENCH.placements, Group.FURNITURE),
        *_parts("mirror", _mirror(), MIRROR.placements, Group.ACCESSORIES),
        *_parts("urn", _garniture_urn(), urn_placements(), Group.ACCESSORIES),
    ]
