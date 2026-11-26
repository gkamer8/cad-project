"""Design data for the bedroom: the single source of truth for model, drawings and spec book.

Coordinates are inches. Origin = south-west interior corner at finished floor;
+x runs east along the 16'-0" walls, +y north along the 12'-0" walls, +z up.
"""

from dataclasses import dataclass
from enum import Enum

import numpy as np

PROJECT = "The Pompeian Bedroom"

ROOM_L = 192.0  # x, 16'-0"
ROOM_W = 144.0  # y, 12'-0"
CEILING_H = 96.0  # 8'-0"

# ------------------------------------------------------------------ vertical zoning (AFF)
BASE_TOP = 7.25  # baseboard
DADO_PANEL = (10.25, 24.25)  # applied panel molding below the chair rail
CHAIR_RAIL_TOP = 30.0  # aligns with window stools
CHAIR_RAIL_H = 2.75
UPPER_PANEL = (34.0, 84.75)  # applied panel molding above the chair rail
CORNICE_BOTTOM = 89.5  # astragal under the dentil course
DENTIL_BOTTOM = 90.0
CROWN_BOTTOM = 91.5

# ------------------------------------------------------------------ openings
WINDOW_W = 32.0
WINDOW_H = 51.0
HEAD_H = 80.0  # window and door heads align at 6'-8"
SILL_H = HEAD_H - WINDOW_H  # 2'-5"
DOOR_W = 36.0
CASING_W = 4.5
REVEAL = 0.25
HEAD_CAP_H = 1.25
PANEL_MARGIN = 4.0  # applied panels sit 4" in from every bay edge


@dataclass(frozen=True)
class WallSide:
    label: str
    start: tuple[float, float]
    direction: tuple[float, float]  # walking direction, room interior on the left
    length: float
    thickness: float

    def point(self, u: float) -> np.ndarray:
        return np.asarray(self.start) + u * np.asarray(self.direction)

    @property
    def inward(self) -> np.ndarray:
        dx, dy = self.direction
        return np.array([-dy, dx])

    def to_world(self, u: float, depth: float, z: float) -> np.ndarray:
        """Wall coordinates (u along the wall, depth into the room, z) -> world xyz."""
        return np.array([*(self.point(u) + depth * self.inward), z])

    def frame(self) -> np.ndarray:
        """4x4 matrix: local x along the wall, local y into the room, local z up."""
        m = np.eye(4)
        m[:2, 0] = self.direction
        m[:2, 1] = self.inward
        m[:2, 3] = self.start
        return m


class Wall(Enum):
    SOUTH = WallSide("South", (0.0, 0.0), (1.0, 0.0), ROOM_L, 6.5)
    EAST = WallSide("East", (ROOM_L, 0.0), (0.0, 1.0), ROOM_W, 4.5)
    NORTH = WallSide("North", (ROOM_L, ROOM_W), (-1.0, 0.0), ROOM_L, 6.5)
    WEST = WallSide("West", (0.0, ROOM_W), (0.0, -1.0), ROOM_W, 4.5)


class OpeningKind(Enum):
    WINDOW = "Window"
    DOOR = "Door"


@dataclass(frozen=True)
class Opening:
    tag: str
    kind: OpeningKind
    wall: Wall
    center_u: float
    width: float
    bottom: float
    top: float

    @property
    def u0(self) -> float:
        return self.center_u - self.width / 2

    @property
    def u1(self) -> float:
        return self.center_u + self.width / 2


def _window(tag: str, wall: Wall, u: float) -> Opening:
    return Opening(tag, OpeningKind.WINDOW, wall, u, WINDOW_W, SILL_H, HEAD_H)


OPENINGS = (
    _window("W1", Wall.SOUTH, 56.0),
    _window("W2", Wall.SOUTH, 136.0),
    _window("W3", Wall.NORTH, 56.0),  # x = 136
    _window("W4", Wall.NORTH, 136.0),  # x = 56
    Opening("D1", OpeningKind.DOOR, Wall.EAST, 72.0, DOOR_W, 0.0, HEAD_H),
)

# Doorcase: fluted pilasters flank the door casing and carry a small entablature.
PILASTER_W = 5.5
PILASTER_PROJ = 1.25
DOORCASE_TOP = 87.0

# Bed-wall bay that receives the damask panel behind the bed (wall u range on WEST).
DAMASK_BAY = (30.0, 114.0)


def openings_on(wall: Wall) -> list[Opening]:
    return [o for o in OPENINGS if o.wall is wall]


def trim_extent(opening: Opening) -> tuple[float, float]:
    """Wall-u range covered by an opening's trim (casing, or the doorcase pilasters)."""
    side = REVEAL + (PILASTER_W if opening.kind is OpeningKind.DOOR else CASING_W)
    return opening.u0 - side, opening.u1 + side


def wall_bays(wall: Wall) -> list[tuple[float, float]]:
    """Plain wall segments between corners and opening trim (and the bed-wall bay lines)."""
    cuts = [0.0]
    for opening in sorted(openings_on(wall), key=lambda o: o.center_u):
        cuts.extend(trim_extent(opening))
    cuts.append(wall.value.length)
    bays = list(zip(cuts[0::2], cuts[1::2]))
    return [(0.0, DAMASK_BAY[0]), DAMASK_BAY, (DAMASK_BAY[1], ROOM_W)] if wall is Wall.WEST else bays


# ------------------------------------------------------------------ furniture & fixtures


@dataclass(frozen=True)
class Placement:
    x: float
    y: float
    z: float
    rotation: float  # degrees about +z; item's local +y (its front) rotates with it

    def matrix(self) -> np.ndarray:
        a = np.radians(self.rotation)
        m = np.eye(4)
        m[:2, :2] = [[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]
        m[:3, 3] = (self.x, self.y, self.z)
        return m


FACING_EAST = -90.0
FACING_WEST = 90.0
FACING_NORTH = 0.0
FACING_SOUTH = 180.0


@dataclass(frozen=True)
class Item:
    tag: str
    name: str
    description: str
    size: tuple[float, float, float]  # W x D x H, inches (local x, local y, z)
    finishes: tuple[str, ...]
    placements: tuple[Placement, ...]


BED = Item(
    "F-1", "Lit a la duchesse (queen)",
    "Louis XVI bed, fluted posts with urn finials, chapeau-de-gendarme headboard upholstered "
    "in oxblood velvet within a gilt-beaded ivory frame; queen mattress 60\" x 80\".",
    (68.0, 88.0, 64.0), ("P-2", "GL-1", "FB-3", "FB-5"),
    (Placement(44.5, 72.0, 0.0, FACING_EAST),),
)
CANOPY = Item(
    "F-2", "Half-tester canopy (ciel de lit)",
    "Wall-hung gilt cornice box with crimson silk valance and gold fringe; champagne silk "
    "side curtains lined in crimson, tied back with gilt tassels.",
    (78.0, 26.0, 8.0), ("GL-1", "FB-2", "FB-4"),
    (Placement(13.0, 72.0, 79.0, FACING_EAST),),
)
NIGHTSTAND = Item(
    "F-3", "Nightstand (pair)",
    "Ebonized commode de chevet, one drawer over open shelf, fluted tapered legs, gilt mounts, "
    "white marble top with pierced brass gallery.",
    (22.0, 16.0, 28.0), ("WD-2", "ST-1", "MT-1"),
    (Placement(9.0, 17.0, 0.0, FACING_EAST), Placement(9.0, 127.0, 0.0, FACING_EAST)),
)
BENCH = Item(
    "F-4", "End-of-bed banquette",
    "Gilt-wood bench, fluted toupie legs, seat upholstered in oxblood velvet with gimp trim.",
    (50.0, 18.0, 19.0), ("GL-1", "FB-3"),
    (Placement(100.0, 72.0, 0.0, FACING_EAST),),
)
COMMODE = Item(
    "F-5", "Commode (pair)",
    "Louis XVI ebonized commode, three drawers, fluted canted stiles, gilt-bronze ring pulls "
    "and escutcheons, white marble top.",
    (40.0, 20.0, 34.0), ("WD-2", "ST-1", "GL-1"),
    (Placement(181.0, 24.0, 0.0, FACING_WEST), Placement(181.0, 120.0, 0.0, FACING_WEST)),
)
MIRROR = Item(
    "F-6", "Oval mirror (pair)",
    "Carved gilt oval frame with beaded sight edge and ribbon-tied laurel crest.",
    (24.0, 2.0, 40.0), ("GL-1", "GZ-2"),
    (Placement(191.0, 24.0, 43.0, FACING_WEST), Placement(191.0, 120.0, 43.0, FACING_WEST)),
)
RUG = Item(
    "R-1", "Area rug",
    "Aubusson-style hand-knotted wool: crimson field, ivory Greek-key border, central rosette.",
    (96.0, 120.0, 0.4), ("RG-1",),
    (Placement(118.0, 72.0, 0.0, FACING_EAST),),
)
CHANDELIER = Item(
    "L-1", "Crystal basket chandelier",
    "Empire basket chandelier, gilt-bronze rings, six candle lights, cut-crystal bead swags; "
    "6 x 40W-eq 2700K flame-tip LED, on dimmer.",
    (22.0, 22.0, 19.0), ("GL-1", "GZ-3", "LT-1", "LT-2"),
    (Placement(96.0, 72.0, CEILING_H, FACING_NORTH),),
)
SCONCE = Item(
    "L-2", "Wall sconce (pair)",
    "Two-arm gilt candle sconce with laurel backplate and red tole mini-shades; 2 x 25W-eq 2700K.",
    (14.0, 7.0, 16.0), ("GL-1", "LS-2", "LT-2"),
    (Placement(96.0, 0.0, 58.0, FACING_NORTH), Placement(96.0, ROOM_W, 58.0, FACING_SOUTH)),
)
BEDSIDE_LAMP = Item(
    "L-3", "Bedside lamp (pair)",
    "Blanc-de-chine urn lamp on gilt base with pleated ivory silk shade; 60W-eq 2700K.",
    (14.0, 14.0, 27.0), ("CR-1", "GL-1", "LS-1"),
    (Placement(8.0, 17.0, 28.0, FACING_EAST), Placement(8.0, 127.0, 28.0, FACING_EAST)),
)
BOUILLOTTE = Item(
    "L-4", "Bouillotte lamp (pair)",
    "Three-light brass bouillotte lamp with adjustable red tole shade and gilt band.",
    (13.0, 13.0, 24.0), ("MT-1", "LS-2", "LT-2"),
    (Placement(180.0, 30.0, 34.0, FACING_WEST), Placement(180.0, 114.0, 34.0, FACING_WEST)),
)

FURNITURE = (BED, CANOPY, NIGHTSTAND, BENCH, COMMODE, MIRROR, RUG)
FIXTURES = (CHANDELIER, SCONCE, BEDSIDE_LAMP, BOUILLOTTE)

# Window treatment: drapery pole just under the cornice, panels stack 10" past the casing.
DRAPE_POLE_Z = 87.25
DRAPE_STACK = 10.0
DRAPE_TIEBACK_Z = 34.0

# Ceiling composition (centred on the room)
CEILING_PANEL_INSET = 16.0
CEILING_RING_R = 30.0
MEDALLION_R = 11.0
CORNER_FAN_R = 14.0
