"""Molding cross-sections (inches), shared by the 3D sweeps and the CAD profile details.

Wall moldings are drawn as closed polygons in (a, b) = (projection into the room,
height). Frame moldings use (a, b) = (width toward the frame interior, projection).
"""

import numpy as np


def quadrant(center, ra: float, rb: float, deg0: float, deg1: float, count: int) -> list:
    t = np.radians(np.linspace(deg0, deg1, count))
    return list(zip(center[0] + ra * np.cos(t), center[1] + rb * np.sin(t)))


def ogee(p0, p1, count: int) -> list:
    """S-curve between two points (vertical tangents at both ends)."""
    t = np.linspace(0.0, 1.0, count)
    s = t * t * (3.0 - 2.0 * t)
    return list(zip(p0[0] + (p1[0] - p0[0]) * s, p0[1] + (p1[1] - p0[1]) * t))


def scaled(profile: np.ndarray, sa: float, sb: float) -> np.ndarray:
    return profile * np.array([sa, sb])


def _poly(points: list) -> np.ndarray:
    """Clean polygon, normalised to counter-clockwise so sweeps get outward normals."""
    pts = np.asarray(points, dtype=float)
    pts = pts[np.r_[True, np.linalg.norm(np.diff(pts, axis=0), axis=1) > 1e-6]]
    area = np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1])
    return pts if area > 0 else pts[::-1]


BASEBOARD = _poly([
    (0.0, 0.0),
    *quadrant((0.75, 0.0), 0.625, 0.625, 0, 90, 7),  # shoe
    (0.75, 5.6), (0.95, 5.75),
    *quadrant((0.95, 5.95), 0.2, 0.2, -90, 90, 7),  # astragal
    *ogee((0.95, 6.15), (0.3, 7.05), 8),  # cyma cap
    (0.3, 7.25), (0.0, 7.25),
])

CHAIR_RAIL = _poly([
    (0.0, 0.0), (0.25, 0.0),
    *quadrant((0.6, 0.0), 0.35, 0.35, 180, 90, 6),  # cove
    (0.75, 0.35),
    *quadrant((0.75, 0.6), 0.25, 0.25, -90, 90, 7),  # bead
    (0.85, 0.98),
    *quadrant((0.85, 1.6), 0.6, 0.6, -90, 90, 11),  # torus nose
    *ogee((0.85, 2.2), (0.3, 2.65), 7),
    (0.3, 2.75), (0.0, 2.75),
])

CROWN = _poly([
    (0.0, 0.0), (0.4, 0.0), (0.4, 0.3),
    *quadrant((0.4, 0.55), 0.25, 0.25, -90, 90, 7),  # bead
    *ogee((0.45, 0.85), (3.85, 3.75), 16),  # cyma recta
    (4.15, 3.75), (4.15, 4.1), (4.5, 4.15), (4.5, 4.5), (0.0, 4.5),
])

ASTRAGAL = _poly([(0.0, 0.0), *quadrant((0.0, 0.25), 0.35, 0.25, -90, 90, 9)])

DENTIL_BACK = _poly([(0.0, 0.0), (0.45, 0.0), (0.45, 1.5), (0.0, 1.5)])

# Architrave casing: a = 0 at the reveal line, negative outward; b = projection.
CASING = _poly([
    (0.0, 0.0), (0.0, 0.45), (-0.2, 0.55), (-2.7, 0.62),
    *quadrant((-2.85, 0.62), 0.15, 0.12, 0, 180, 5),  # quirk bead
    (-3.35, 0.7), (-3.35, 0.82),
    *ogee((-3.35, 0.82), (-3.9, 1.12), 6),
    *quadrant((-4.2, 1.12), 0.3, 0.06, 0, 90, 3),
    (-4.5, 1.18), (-4.5, 0.0),
])

# Applied wall-panel molding: a toward the panel interior, b = projection.
PANEL = _poly([
    (0.0, 0.0), (0.0, 0.28),
    *quadrant((0.15, 0.28), 0.15, 0.14, 180, 90, 5),
    *ogee((0.2, 0.42), (1.05, 0.66), 8),
    (1.3, 0.66),
    *quadrant((1.3, 0.16), 0.45, 0.5, 90, 0, 6),
    (1.75, 0.0),
])
DADO_PANEL = scaled(PANEL, 1.25 / 1.75, 0.5 / 0.66)
CEILING_PANEL = scaled(PANEL, 2.5 / 1.75, 0.8 / 0.66)

# Small cornice used on window / door heads (a outward from the supporting block).
HEAD_CAP = _poly([
    (-0.6, 0.0), (0.15, 0.0),
    *quadrant((0.15, 0.4), 0.4, 0.4, -90, 0, 5),  # ovolo
    (0.65, 0.45), (0.65, 0.7),
    *quadrant((1.1, 0.7), 0.45, 0.55, 180, 90, 6),  # cove
    (1.15, 1.25), (-0.6, 1.25),
])

# Gilt frame for mirrors and pictures: a inward from the outer edge, b = projection.
GILT_FRAME = _poly([
    (0.0, 0.0), (0.0, 0.5),
    *quadrant((0.45, 0.5), 0.45, 0.55, 180, 90, 7),  # outer ovolo
    (0.9, 1.05), (1.2, 0.95),
    *quadrant((1.55, 0.95), 0.35, 0.3, 180, 360, 7),  # scotia hollow
    (1.95, 0.9),
    *quadrant((2.1, 0.9), 0.15, 0.15, 180, 0, 6),  # sight-edge bead
    (2.25, 0.4), (2.4, 0.0),
])

# Bead used for gilt beading on furniture frames and the canopy (a, b both small).
BEAD = _poly([(0.0, 0.0), *quadrant((0.0, 0.0), 0.25, 0.3, 0, 180, 9)])

# Canopy cornice box face (a outward from the box outline, b height from box bottom).
CANOPY_CORNICE = _poly([
    (-0.5, 0.0), (0.3, 0.0),
    *quadrant((0.3, 0.35), 0.35, 0.35, -90, 90, 7),  # bead
    (0.3, 0.9),
    *ogee((0.3, 0.9), (1.9, 6.1), 14),
    (2.4, 6.2), (2.4, 6.7), (2.1, 6.8), (2.1, 7.6), (2.5, 7.7), (2.5, 8.0), (-0.5, 8.0),
])

# Doorcase / pilaster moldings (a outward from the shaft outline, b height).
PILASTER_BASE = _poly([
    (-0.5, 0.0), (0.55, 0.0), (0.55, 0.5),
    *quadrant((0.35, 0.85), 0.35, 0.35, -90, 90, 7),  # torus
    (0.25, 1.25), (0.12, 1.45), (0.12, 1.75), (-0.5, 1.75),
])
PILASTER_CAPITAL = _poly([
    (-0.5, 0.0), (0.12, 0.0), (0.12, 0.3),
    *quadrant((0.12, 0.55), 0.22, 0.25, -90, 90, 6),  # astragal
    (0.15, 0.85), (0.15, 1.6),
    *quadrant((0.45, 1.6), 0.3, 0.45, 180, 90, 6),  # echinus
    (0.65, 2.05), (0.65, 2.75), (-0.5, 2.75),
])
ENTABLATURE_CORNICE = _poly([
    (-0.5, 0.0), (0.2, 0.0),
    *quadrant((0.2, 0.35), 0.35, 0.35, -90, 0, 5),
    (0.6, 0.45), (0.6, 0.75),
    *ogee((0.6, 0.75), (2.4, 1.7), 9),
    (2.6, 1.75), (2.6, 2.0), (-0.5, 2.0),
])

# Tabletop edge (marble): a outward from the top outline, b height from slab bottom.
SLAB_EDGE = _poly([
    (-0.75, 0.0), (0.05, 0.0),
    *quadrant((0.05, 0.3), 0.3, 0.3, -90, 0, 5),
    (0.35, 0.55),
    *ogee((0.35, 0.55), (0.6, 1.0), 6),
    (0.6, 1.1), (0.5, 1.2), (-0.75, 1.2),
])

DETAILED_PROFILES = (
    ("CROWN MOLDING", CROWN),
    ("CHAIR RAIL", CHAIR_RAIL),
    ("BASEBOARD", BASEBOARD),
    ("WINDOW / DOOR CASING", CASING),
    ("UPPER WALL PANEL MOLDING", PANEL),
    ("WINDOW HEAD CAP", HEAD_CAP),
)
