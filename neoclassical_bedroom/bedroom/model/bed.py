"""F-1 lit a la duchesse with bedding, and F-2 the half-tester canopy above it.

Bed-local frame: origin at the footprint centre on the floor, +y toward the foot,
x across the width. Canopy-local frame: origin 13" off the wall at the canopy base.
"""

import numpy as np

from ..geom.mesh import Mesh
from ..geom.prims import box, grid, loft, sweep, tube, wave_noise
from ..spec import BED, CANOPY
from . import profiles
from .drapery import Drape, drape_mesh, tassel
from .kit import (bed_post, bow, chapeau, finial_urn, frame_moulding, outline_path, padded_panel, part_at,
                  pillow, soft_box, turned, wreath)
from .parts import Group, Mat, Part, Shading

HALF_W = BED.size[0] / 2
HEAD_Y, FOOT_Y = -BED.size[1] / 2 + 1.75, BED.size[1] / 2 - 1.75
POST_X = HALF_W - 1.75
MATTRESS_TOP = 26.0
FLIP_Z = np.diag([1.0, 1.0, -1.0, 1.0])


def _rot_x(deg: float) -> np.ndarray:
    a = np.radians(deg)
    m = np.eye(4)
    m[1:3, 1:3] = [[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]
    return m


def _axis_x(direction: float) -> np.ndarray:
    m = np.eye(4)
    m[:3, :3] = [[0, 0, direction], [0, 1, 0], [-direction, 0, 0]]
    return m


def _with_wrinkles(mesh: Mesh, seed: int, scale: float, amplitude: float) -> Mesh:
    dz = wave_noise(mesh.verts, seed, scale, amplitude)
    return Mesh(mesh.verts + np.c_[np.zeros((len(dz), 2)), dz], mesh.loops, mesh.sizes)


def _along_y(section: np.ndarray, ys: np.ndarray) -> Mesh:
    """Extrude a closed (x, z) section along +y."""
    return loft(np.stack([np.c_[section[:, 0], np.full(len(section), y), section[:, 1]] for y in ys]))


def _drape_section(half_w: float, top: float, drop: float, thickness: float, radius: float) -> np.ndarray:
    """Closed (x, z) section of bedding laid over the mattress and hanging down both sides."""
    t = np.linspace(0, np.pi / 2, 7)
    outer = ([(-half_w, top - drop)]
             + [(-half_w + radius - radius * np.cos(a), top - radius + radius * np.sin(a)) for a in t[1:]]
             + [(half_w - radius + radius * np.sin(a), top - radius + radius * np.cos(a)) for a in t[:-1]]
             + [(half_w, top - drop)])
    inner = [(x * (half_w - thickness) / half_w, z - thickness) for x, z in outer[::-1]]
    return np.array(outer + inner)


def _board(top_fn, bottom: float, plane_y: float) -> dict[Mat, list[Mesh]]:
    """Gilt frame, ivory backing and velvet padded panel of a head- or footboard."""
    half = POST_X - 1.6
    frame = frame_moulding(outline_path(half, bottom, top_fn, 0.0), 0.95)
    panel = padded_panel(half - 2.0, bottom + 2.0, lambda x: top_fn(x) - 2.0, 0.0, 2.2, 0.9)
    backing = padded_panel(half + 0.4, bottom - 0.4, lambda x: top_fn(x) + 0.4, -1.0, 1.4, 0.0)
    return {Mat.GILT: [frame.moved((0, plane_y, 0))], Mat.TRIM_IVORY: [backing.moved((0, plane_y, 0))],
            Mat.VELVET: [panel.moved((0, plane_y, 0))]}


def _bed_frame() -> dict[Mat, list[Mesh]]:
    out = {Mat.GILT: [], Mat.TRIM_IVORY: [], Mat.VELVET: []}
    for x in (-POST_X, POST_X):
        out[Mat.TRIM_IVORY] += [bed_post(58.0, 1.75).moved((x, HEAD_Y, 0)), bed_post(34.0, 1.6).moved((x, FOOT_Y, 0))]
        out[Mat.GILT] += [finial_urn(1.5).moved((x, HEAD_Y, 58.0)), finial_urn(1.15).moved((x, FOOT_Y, 34.0))]
        rail_x = x - np.sign(x) * 1.2
        out[Mat.TRIM_IVORY].append(box((rail_x - 0.6, HEAD_Y + 1.5, 9.0), (rail_x + 0.6, FOOT_Y - 1.5, 16.0)))
        bead = np.array([[rail_x, FOOT_Y - 1.5, 16.0], [rail_x, HEAD_Y + 1.5, 16.0]])
        out[Mat.GILT].append(sweep(profiles.BEAD, bead, (0, 0, 1), closed=False))
    for y in (HEAD_Y + 1.5, FOOT_Y - 1.5):
        out[Mat.TRIM_IVORY].append(box((-POST_X + 1, y - 0.6, 9.0), (POST_X - 1, y + 0.6, 16.0)))
    head_top = lambda x: chapeau(np.asarray(x, float), POST_X - 1.6, 50.0, 7.0)
    foot_top = lambda x: chapeau(np.asarray(x, float), POST_X - 1.6, 27.5, 3.5)
    for board in (_board(head_top, 20.0, HEAD_Y), _board(foot_top, 13.0, FOOT_Y)):
        for mat, meshes in board.items():
            out[mat] += meshes
    crest = wreath(2.4, 1.4, 14) + [m.moved((0, 0, 3.0)) for m in bow(4.5)]
    out[Mat.GILT] += [m.moved((0, HEAD_Y + 0.9, 59.6)) for m in crest]
    return out


def _bedding() -> dict[Mat, list[Mesh]]:
    out = {Mat.LINEN: [], Mat.VELVET: [], Mat.DAMASK: [], Mat.GILT: []}
    out[Mat.LINEN].append(soft_box((-30.5, HEAD_Y + 1.6, 16.0), (30.5, FOOT_Y - 1.6, MATTRESS_TOP), 0.12))
    duvet = _along_y(_drape_section(32.6, MATTRESS_TOP + 1.6, 11.0, 1.4, 2.6), np.linspace(-14.0, FOOT_Y - 2.0, 40))
    cuff = _along_y(_drape_section(32.9, MATTRESS_TOP + 2.3, 11.2, 1.0, 2.4), np.linspace(-17.5, -12.5, 6))
    throw = _along_y(_drape_section(34.4, MATTRESS_TOP + 2.5, 15.0, 0.8, 3.2), np.linspace(24.0, 37.0, 14))
    out[Mat.LINEN] += [_with_wrinkles(duvet, 3, 5.0, 0.35), cuff]
    out[Mat.VELVET].append(_with_wrinkles(throw, 9, 4.0, 0.25))
    for side, seed in ((-1, 1), (1, 2)):
        sham = pillow((26.0, 26.0, 6.5), seed).transformed(_rot_x(-72.0))
        out[Mat.DAMASK].append(sham.moved((side * 14.2, HEAD_Y + 6.0, MATTRESS_TOP + 13.5)))
        sleep = pillow((29.0, 20.0, 7.5), seed + 5).transformed(_rot_x(-28.0))
        out[Mat.LINEN].append(sleep.moved((side * 14.6, HEAD_Y + 15.5, MATTRESS_TOP + 6.0)))
        cap = turned([(0.05, 0.0), (1.3, 0.0), (1.1, 0.5), (0.4, 0.8), (0.05, 0.85)], 20).transformed(_axis_x(side))
        out[Mat.GILT].append(cap.moved((side * 17.0, HEAD_Y + 22.5, MATTRESS_TOP + 5.0)))
        out[Mat.GILT].append(tassel().transformed(FLIP_Z).moved((side * 17.9, HEAD_Y + 22.5, MATTRESS_TOP + 5.0)))
    bolster = turned([(0.1, -17.0), (2.6, -17.0), (3.6, -16.3), (4.0, -15.0), (4.0, 15.0), (3.6, 16.3),
                      (2.6, 17.0), (0.1, 17.0)], 40)
    out[Mat.VELVET].append(bolster.transformed(_axis_x(1.0)).moved((0, HEAD_Y + 22.5, MATTRESS_TOP + 5.0)))
    return out


# ------------------------------------------------------------------ canopy (ciel de lit)
BOX_HALF, BOX_BACK, BOX_FRONT = 37.5, -13.0, 11.5


def _rounded_u(offset: float, radius: float) -> np.ndarray:
    """Plan path wrapping the cornice box (back -> side -> front -> side -> back), corners rounded."""
    hx, fy = BOX_HALF + offset, BOX_FRONT + offset
    t = np.linspace(0, np.pi / 2, 8)
    left = [(-hx, BOX_BACK)] + [(-hx + radius - radius * np.cos(a), fy - radius + radius * np.sin(a)) for a in t]
    right = [(hx - radius + radius * np.sin(a), fy - radius + radius * np.cos(a)) for a in t] + [(hx, BOX_BACK)]
    pts = np.array(left + right)
    seg = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    s = np.arange(0.0, seg[-1], 0.3)
    return np.c_[np.interp(s, seg, pts[:, 0]), np.interp(s, seg, pts[:, 1])]


def _valance(offset: float, top: float, depth: float, scallop: float, pleat: float) -> Mesh:
    path = _rounded_u(offset, 2.5)
    tangent = np.gradient(path, axis=0)
    normal = np.c_[tangent[:, 1], -tangent[:, 0]] / np.linalg.norm(tangent, axis=1, keepdims=True)
    s = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))]
    bottom = top - depth + scallop * np.abs(np.sin(np.pi * s / 9.6))
    rows = []
    for k in np.linspace(0, 1, 14):
        z = top + (bottom - top) * k
        wave = pleat * np.sin(2 * np.pi * s / 2.4) * (0.4 + 0.6 * k)
        rows.append(np.c_[path + normal * wave[:, None], z])
    return grid(np.stack(rows, axis=1), wrap_rows=False, wrap_cols=False)


def _canopy() -> dict[Mat, list[Mesh]]:
    out = {Mat.GILT: [], Mat.SILK_RED: [], Mat.SILK_IVORY: [], Mat.TRIM_IVORY: []}
    out[Mat.TRIM_IVORY].append(box((-BOX_HALF, BOX_BACK, 0.0), (BOX_HALF, BOX_FRONT, 8.0)))
    u_path = np.array([[-BOX_HALF, BOX_BACK, 0.0], [-BOX_HALF, BOX_FRONT, 0.0], [BOX_HALF, BOX_FRONT, 0.0],
                       [BOX_HALF, BOX_BACK, 0.0]])
    out[Mat.GILT].append(sweep(profiles.CANOPY_CORNICE, u_path, (0, 0, 1), closed=False))
    crest = wreath(3.0, 1.7, 16) + [m.moved((0, 0, 3.6)) for m in bow(5.5)]
    out[Mat.GILT] += [m.moved((0, BOX_FRONT + 1.0, 11.6)) for m in crest]
    out[Mat.GILT] += [finial_urn(1.2).moved((x, BOX_FRONT, 8.0)) for x in (-BOX_HALF + 1.5, BOX_HALF - 1.5)]
    out[Mat.SILK_RED].append(_valance(2.7, 0.6, 9.0, 2.4, 0.45))
    out[Mat.GILT].append(_valance(2.85, -6.2, 8.0, 2.4, 0.5))  # bullion fringe below the scallops
    out[Mat.SILK_IVORY].append(box((-BOX_HALF + 0.5, BOX_BACK, -0.6), (BOX_HALF - 0.5, BOX_FRONT, -0.1)))
    floor = -CANOPY.placements[0].z
    plane = BOX_HALF - 0.7
    for side in (-1.0, 1.0):
        drape = Drape(z_top=-0.5, z_tie=46.0 + floor, z_bottom=floor + 0.4, span_top=(-12.6, 11.0),
                      span_tie=(-11.2, -5.4), span_bottom=(-12.8, 1.5), depth=(0.0, 2.4, 0.9),
                      fabric_width=62.0, folds=8, seed=40 + int(side))
        to_canopy = np.eye(4)  # drape (a, d, z) -> canopy (x = side*plane - side*d, y = a, z)
        to_canopy[:3, :3] = [[0, -side, 0], [1, 0, 0], [0, 0, 1]]
        to_canopy[0, 3] = side * plane
        out[Mat.SILK_IVORY].append(drape_mesh(drape).transformed(to_canopy))
        tie_a, tie_z = -8.3, drape.z_tie
        tie_x = side * (BOX_HALF - 0.7) - side * 2.4
        loop = np.c_[tie_x + 2.8 * np.cos(np.linspace(0, 2 * np.pi, 33)),
                     tie_a + 3.6 * np.sin(np.linspace(0, 2 * np.pi, 33)), np.full(33, tie_z)]
        out[Mat.GILT].append(tube(loop, 0.32, 8))
        out[Mat.GILT].append(tassel().transformed(FLIP_Z).moved((tie_x - side * 2.9, tie_a, tie_z - 0.3)))
    return out


def _parts(name: str, meshes_by_mat: dict[Mat, list[Mesh]], where, group_by_mat, shading_by_mat) -> list[Part]:
    return [part_at(f"{name}_{mat.name.lower()}", meshes, where, mat, group_by_mat[mat], shading_by_mat[mat])
            for mat, meshes in meshes_by_mat.items()]


SHADING = {Mat.GILT: Shading.CRISP, Mat.TRIM_IVORY: Shading.CRISP, Mat.VELVET: Shading.SOFT,
           Mat.LINEN: Shading.SOFT, Mat.DAMASK: Shading.SOFT, Mat.SILK_RED: Shading.SOFT,
           Mat.SILK_IVORY: Shading.SOFT}
GROUP = {Mat.GILT: Group.FURNITURE, Mat.TRIM_IVORY: Group.FURNITURE, Mat.VELVET: Group.FURNITURE,
         Mat.LINEN: Group.SOFT_GOODS, Mat.DAMASK: Group.SOFT_GOODS, Mat.SILK_RED: Group.SOFT_GOODS,
         Mat.SILK_IVORY: Group.SOFT_GOODS}


def bed_parts() -> list[Part]:
    frame = _bed_frame()
    bedding = _bedding()
    return [
        *_parts("bed_frame", frame, BED.placements, GROUP, SHADING),
        *_parts("bedding", bedding, BED.placements, GROUP, SHADING),
        *_parts("canopy", _canopy(), CANOPY.placements, GROUP, SHADING),
    ]
