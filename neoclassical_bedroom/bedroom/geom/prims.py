"""Parametric primitives: boxes, prisms, lofts, sweeps, lathes, tubes and soft shapes.

Everything is expressed as rings of points that are lofted into quads, so a molding
sweep, a turned bed post and a bolster pillow all share the same topology code.
"""

from collections.abc import Callable

import numpy as np

from .mesh import Mesh, from_faces

TAU = 2.0 * np.pi


def unit(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def grid(points: np.ndarray, wrap_rows: bool, wrap_cols: bool) -> Mesh:
    """Quad surface through a (rows, cols, 3) lattice, optionally closed in either direction."""
    rows, cols = points.shape[:2]
    idx = np.arange(rows * cols).reshape(rows, cols)
    idx = np.vstack([idx, idx[:1]]) if wrap_rows else idx
    idx = np.hstack([idx, idx[:, :1]]) if wrap_cols else idx
    # Winding: across a ring first, then along the rows -> outward normals for
    # counter-clockwise rings / profiles (lathes, sweeps, tubes, prisms alike).
    quads = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], axis=-1).reshape(-1, 4)
    return Mesh(points.reshape(-1, 3).astype(float), quads.ravel(), np.full(len(quads), 4))


def loft(rings: np.ndarray) -> Mesh:
    """Closed solid through (m, k, 3) rings: side quads plus an n-gon cap at both ends."""
    m, k = rings.shape[:2]
    side = grid(rings, wrap_rows=False, wrap_cols=True)
    caps = np.concatenate([np.arange(k)[::-1], np.arange((m - 1) * k, m * k)])
    return Mesh(side.verts, np.concatenate([side.loops, caps]), np.concatenate([side.sizes, [k, k]]))


def box(lo, hi) -> Mesh:
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    verts = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
             [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]]
    faces = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    return from_faces(verts, faces)


def prism(polygon_xy, z0: float, z1: float) -> Mesh:
    """Vertical extrusion of a (counter-clockwise) 2D polygon."""
    p = np.asarray(polygon_xy, dtype=float)
    rings = np.stack([np.c_[p, np.full(len(p), z0)], np.c_[p, np.full(len(p), z1)]])
    return loft(rings)


def sweep_rings(profile, path, normal, closed: bool) -> np.ndarray:
    """Mitred placement of a 2D profile (a, b) along a planar path.

    ``a`` runs to the left of the path direction (``normal x direction``) and ``b``
    along ``normal``; at every corner the profile is stretched along the bisector so
    that mitres stay true, exactly like a joiner's mitred molding.
    """
    pts = np.asarray(path, dtype=float)
    n = unit(np.asarray(normal, dtype=float))
    ends = np.vstack([pts, pts[:1]]) if closed else pts
    left = np.cross(n, unit(np.diff(ends, axis=0)))
    l_in = np.roll(left, 1, axis=0) if closed else np.vstack([left[:1], left])
    l_out = left if closed else np.vstack([left, left[-1:]])
    bis = unit(l_in + l_out)
    stretch = 1.0 / np.einsum("ij,ij->i", bis, l_in)
    prof = np.asarray(profile, dtype=float)
    across = (stretch[:, None] * bis)[:, None, :] * prof[None, :, 0:1]
    return pts[:, None, :] + across + prof[None, :, 1:2] * n


def sweep(profile, path, normal, closed: bool) -> Mesh:
    rings = sweep_rings(profile, path, normal, closed)
    return grid(rings, wrap_rows=True, wrap_cols=True) if closed else loft(rings)


def lathe(profile_rz, segments: int, modulation: Callable) -> Mesh:
    """Surface of revolution about +z; ``modulation(theta, z)`` scales the radius (flutes)."""
    prof = np.asarray(profile_rz, dtype=float)
    theta = np.linspace(0.0, TAU, segments, endpoint=False)
    radius = prof[:, 0:1] * modulation(theta[None, :], prof[:, 1:2])
    height = np.broadcast_to(prof[:, 1:2], radius.shape)
    return loft(np.stack([radius * np.cos(theta), radius * np.sin(theta), height], axis=-1))


def smooth_turning(theta: np.ndarray, z: np.ndarray) -> np.ndarray:
    return np.ones(np.broadcast_shapes(theta.shape, z.shape))


def fluted(count: int, depth_ratio: float, z0: float, z1: float) -> Callable:
    """Concave flutes between z0 and z1 with rounded (faded) terminations."""

    def modulation(theta: np.ndarray, z: np.ndarray) -> np.ndarray:
        groove = np.sqrt(np.clip((np.cos(count * theta) - 0.15) / 0.85, 0.0, 1.0))
        span = np.clip((z - z0) / (z1 - z0), 0.0, 1.0)
        fade = np.clip(np.minimum(span, 1.0 - span) * 12.0, 0.0, 1.0)
        return 1.0 - depth_ratio * groove * fade

    return modulation


def tube(path, radius, sides: int) -> Mesh:
    """Round tube along a 3D path using parallel-transport frames (radius may vary per point)."""
    pts = np.asarray(path, dtype=float)
    tangents = unit(np.gradient(pts, axis=0))
    seed = np.cross(tangents[0], [0.0, 0.0, 1.0] if abs(tangents[0][2]) < 0.9 else [1.0, 0.0, 0.0])
    normals = [unit(seed)]
    for t in tangents[1:]:
        normals.append(unit(normals[-1] - np.dot(normals[-1], t) * t))
    normals = np.asarray(normals)
    binormals = np.cross(tangents, normals)
    theta = np.linspace(0.0, TAU, sides, endpoint=False)
    r = np.broadcast_to(np.asarray(radius, dtype=float), (len(pts),))[:, None, None]
    ring = np.cos(theta)[None, :, None] * normals[:, None, :] + np.sin(theta)[None, :, None] * binormals[:, None, :]
    return loft(pts[:, None, :] + r * ring)


def _signed_pow(values: np.ndarray, exponent: float) -> np.ndarray:
    return np.sign(values) * np.abs(values) ** exponent


def superellipsoid(size, e_vertical: float, e_horizontal: float, rows: int, cols: int) -> Mesh:
    """Rounded box / cushion / lens centred on the origin with overall dimensions ``size``."""
    half = np.asarray(size, dtype=float) / 2.0
    eta = np.linspace(-np.pi / 2, np.pi / 2, rows + 2)[1:-1]
    omega = np.linspace(-np.pi, np.pi, cols, endpoint=False)
    ce, se = _signed_pow(np.cos(eta), e_vertical)[:, None], _signed_pow(np.sin(eta), e_vertical)[:, None]
    co, so = _signed_pow(np.cos(omega), e_horizontal)[None, :], _signed_pow(np.sin(omega), e_horizontal)[None, :]
    pts = np.stack([half[0] * ce * co, half[1] * ce * so, half[2] * se * np.ones_like(co)], axis=-1)
    return loft(pts)




def arc(center, radius: float, deg0: float, deg1: float, count: int) -> np.ndarray:
    a = np.radians(np.linspace(deg0, deg1, count))
    c = np.asarray(center, dtype=float)
    return np.c_[c[0] + radius * np.cos(a), c[1] + radius * np.sin(a), np.full(count, c[2])]




def wave_noise(points: np.ndarray, seed: int, scale: float, amplitude: float) -> np.ndarray:
    """Cheap smooth pseudo-noise (sum of random sinusoids) for fabric wrinkles."""
    rng = np.random.default_rng(seed)
    total = np.zeros(len(points))
    for _ in range(6):
        k = rng.normal(size=3)
        k = k / np.linalg.norm(k) * rng.uniform(0.6, 1.6) / scale
        total += np.sin(points @ k + rng.uniform(0, TAU))
    return amplitude * total / 6.0
