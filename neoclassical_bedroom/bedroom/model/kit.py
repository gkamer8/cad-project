"""Reusable furniture components: turned legs, finials, padded panels, cushions, wreaths."""

import numpy as np

from ..geom.mesh import Mesh, merge
from ..geom.prims import fluted, grid, lathe, loft, smooth_turning, superellipsoid, sweep, tube
from ..spec import Placement
from . import profiles
from .parts import Group, Mat, Part, Shading


def placed(mesh: Mesh, where: Placement) -> Mesh:
    return mesh.transformed(where.matrix())


def part_at(name: str, meshes: list[Mesh], placements, mat: Mat, group: Group, shading: Shading) -> Part:
    """One part holding the component copied to every placement of an item."""
    return Part(name, merge([placed(m, p) for p in placements for m in meshes]), mat, group, shading)


def turned_leg(height: float, top_r: float, foot_r: float) -> Mesh:
    """Louis XVI leg: toupie foot, fluted tapering shaft, collar and block top."""
    h = height
    prof = [(foot_r * 0.55, 0.0), (foot_r * 1.1, 0.35), (foot_r * 1.25, 0.9), (foot_r * 0.9, 1.6),
            (foot_r * 0.75, 1.85), (foot_r * 1.05, 2.05), (foot_r * 0.95, 2.35), (foot_r, 2.6),
            (top_r * 0.92, h - 3.0), (top_r * 1.2, h - 2.75), (top_r * 1.2, h - 2.35), (top_r, h - 2.15),
            (top_r * 1.05, h - 1.6), (top_r * 1.05, h)]
    return lathe(prof, 32, fluted(8, 0.07, 2.7, h - 3.1))


def finial_urn(scale: float) -> Mesh:
    prof = [(0.05, 0.0), (0.9, 0.0), (0.9, 0.25), (0.55, 0.45), (0.45, 0.8), (1.05, 1.35), (1.2, 1.9),
            (0.95, 2.45), (0.55, 2.65), (0.7, 2.85), (0.4, 3.2), (0.55, 3.55), (0.3, 4.0), (0.05, 4.15)]
    return lathe([(r * scale, z * scale) for r, z in prof], 28, fluted(10, 0.08, 1.4 * scale, 2.3 * scale))


def bed_post(height: float, radius: float) -> Mesh:
    prof = [(radius * 0.75, 0.0), (radius * 1.15, 0.5), (radius * 1.25, 1.3), (radius * 0.9, 2.2),
            (radius * 1.05, 2.6), (radius * 1.05, 3.6), (radius * 0.9, 4.0), (radius, 4.4),
            (radius * 0.86, height - 3.4), (radius * 1.12, height - 3.0), (radius * 1.12, height - 2.4),
            (radius * 0.95, height - 2.1), (radius * 1.25, height - 1.2), (radius * 1.25, height)]
    return lathe(prof, 36, fluted(12, 0.06, 4.6, height - 3.6))


def chapeau(x: np.ndarray, half_w: float, shoulder: float, crown: float) -> np.ndarray:
    """Louis XVI 'chapeau de gendarme' top line: flat shoulders rising to a central arch."""
    t = np.clip(np.abs(x) / half_w, 0, 1)
    return shoulder + crown * np.exp(-(x / (half_w * 0.48)) ** 2) - 0.6 * t ** 4


def outline_path(half_w: float, bottom: float, top_fn, plane_y: float) -> np.ndarray:
    """Closed outline in a vertical plane, counter-clockwise for a viewer at +y."""
    xs = np.linspace(-half_w, half_w, 41)
    pts = [(half_w, bottom), (-half_w, bottom)] + [(x, float(top_fn(x))) for x in xs]
    return np.array([(x, plane_y, z) for x, z in pts])


def padded_panel(half_w: float, bottom: float, top_fn, plane_y: float, thickness: float, puff: float) -> Mesh:
    """Upholstered panel: a rounded cushion stretched to follow a shaped top line."""
    cushion = superellipsoid((2 * half_w, thickness, 1.0), 0.18, 0.18, 26, 64)
    v = cushion.verts.copy()
    top = top_fn(v[:, 0])
    t = v[:, 2] + 0.5
    v[:, 2] = bottom + t * (top - bottom)
    bulge = np.clip(1 - (v[:, 0] / half_w) ** 2, 0, 1) * np.clip(1 - (2 * t - 1) ** 2, 0, 1)
    front = v[:, 1] > 0
    v[:, 1] = v[:, 1] + plane_y + front * puff * bulge
    return Mesh(v, cushion.loops, cushion.sizes)


def pillow(size, seed: int) -> Mesh:
    """Lying pillow (x by y, thickness z) with gently pinched corners and wrinkles."""
    shape = superellipsoid(size, 0.9, 0.32, 20, 48)
    v = shape.verts.copy()
    hx, hy = size[0] / 2, size[1] / 2
    corner = (np.abs(v[:, 0]) / hx) ** 2 * (np.abs(v[:, 1]) / hy) ** 2
    v[:, 2] *= 1.0 - 0.45 * corner
    rng = np.random.default_rng(seed)
    v[:, 2] += 0.12 * np.sin(v[:, 0] * rng.uniform(0.6, 0.9) + rng.uniform(0, 6)) * (1 - corner)
    return Mesh(v, shape.loops, shape.sizes)


def cushion(size, roundness: float) -> Mesh:
    return superellipsoid(size, roundness, roundness * 0.6, 18, 48)


def frame_moulding(outline: np.ndarray, scale: float) -> Mesh:
    """Gilt frame swept around a closed outline lying in a plane facing +y."""
    return sweep(profiles.scaled(profiles.GILT_FRAME, scale, scale), outline, (0, 1, 0), closed=True)


def wreath(radius: float, leaf: float, count: int) -> list[Mesh]:
    """Laurel wreath in the x-z plane (facing +y): stem ring plus paired leaves."""
    ring = np.array([[radius * np.cos(t), 0.0, radius * np.sin(t)] for t in np.linspace(0, 2 * np.pi, 49)])
    pieces = [tube(ring, leaf * 0.12, 8)]
    for t in np.linspace(0, 2 * np.pi, count, endpoint=False):
        for side in (-1, 1):
            leaf_mesh = superellipsoid((leaf, leaf * 0.22, leaf * 0.38), 0.8, 0.9, 6, 10)
            ang = t + side * 0.35
            m = np.eye(4)
            m[:3, :3] = _rot_y(-(t + np.pi / 2 + side * 0.55))
            m[:3, 3] = ((radius + side * leaf * 0.25) * np.cos(ang), 0.0, (radius + side * leaf * 0.25) * np.sin(ang))
            pieces.append(leaf_mesh.transformed(m))
    return pieces


def _rot_y(a: float) -> np.ndarray:
    return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])


def bow(width: float) -> list[Mesh]:
    """Ribbon bow (two loops and two tails) in the x-z plane."""
    t = np.linspace(0, 2 * np.pi, 33)
    loops = [np.c_[side * (width * 0.25 + width * 0.25 * np.cos(t)), 0.15 * np.sin(2 * t), width * 0.16 * np.sin(t)]
             for side in (-1, 1)]
    tails = [np.c_[side * np.linspace(0.2, width * 0.4, 12), np.zeros(12), -np.linspace(0.2, width * 0.55, 12)]
             for side in (-1, 1)]
    return [tube(p, width * 0.045, 8) for p in loops + tails] + [superellipsoid((0.5, 0.4, 0.5), 1, 1, 6, 8)]


def soft_box(lo, hi, roundness: float) -> Mesh:
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return superellipsoid(hi - lo, roundness, roundness, 14, 40).moved((lo + hi) / 2)


def turned(profile, segments: int) -> Mesh:
    return lathe(profile, segments, smooth_turning)






def revolve_open(profile_rz, segments: int, modulation) -> Mesh:
    """Open surface of revolution (shades, cups): no end caps, thin two-sided shell."""
    prof = np.asarray(profile_rz, dtype=float)
    theta = np.linspace(0.0, 2 * np.pi, segments, endpoint=False)
    radius = prof[:, 0:1] * modulation(theta[None, :], prof[:, 1:2])
    height = np.broadcast_to(prof[:, 1:2], radius.shape)
    return grid(np.stack([radius * np.cos(theta), radius * np.sin(theta), height], axis=-1),
                wrap_rows=False, wrap_cols=True)


def ring(radius: float, z: float, thickness: float) -> Mesh:
    """Closed torus-like ring (tube along a full circle)."""
    t = np.linspace(0, 2 * np.pi, 65)
    return tube(np.c_[radius * np.cos(t), radius * np.sin(t), np.full(65, z)], thickness, 10)


def bead(radius: float) -> Mesh:
    return superellipsoid((2 * radius, 2 * radius, 2.3 * radius), 1.0, 1.0, 5, 8)
