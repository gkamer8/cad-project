"""Typed vocabulary shared by the 3D model, the renderer, the CAD set and the spec book."""

from dataclasses import dataclass
from enum import Enum

from ..geom.mesh import Mesh


@dataclass(frozen=True)
class Finish:
    code: str  # finish-schedule tag printed on drawings
    name: str
    description: str
    hex_color: str  # sRGB display colour (also the base colour of exported meshes)


class Mat(Enum):
    """Every surface in the room. Codes follow interior-design finish-schedule practice."""

    WALL_RED = Finish("P-1", "Pompeian Red", "Wall paint, eggshell, above chair rail", "#8E2B22")
    TRIM_IVORY = Finish("P-2", "Antique Ivory", "Trim / millwork enamel, satin", "#EDE3CF")
    CEILING = Finish("P-3", "Pale Ivory", "Ceiling paint, flat", "#F4EEE2")
    GILT = Finish("GL-1", "Water Gilt", "23k gold leaf over red bole, burnished", "#C9A04E")
    PARQUET = Finish("WD-1", "Herringbone Oak", "White oak parquet, honey stain, satin", "#9C6B3E")
    LACQUER = Finish("WD-2", "Ebonized Lacquer", "Black lacquer case goods, hand-rubbed", "#17120F")
    MARBLE = Finish("ST-1", "Statuario Marble", "White marble tops, polished, ogee edge", "#EDEAE6")
    DAMASK = Finish("FB-1", "Silk Damask", "Red-on-red silk damask wall upholstery", "#7A1A1C")
    SILK_RED = Finish("FB-2", "Crimson Silk", "Silk taffeta drapery, interlined", "#7D0F1A")
    VELVET = Finish("FB-3", "Garnet Velvet", "Cotton velvet upholstery", "#7A1421")
    SILK_IVORY = Finish("FB-4", "Champagne Silk", "Canopy curtains and drapery linings", "#E9DCC2")
    LINEN = Finish("FB-5", "Ivory Sateen", "Bedding, 600tc cotton sateen", "#F1EBDF")
    RUG = Finish("RG-1", "Aubusson-style Rug", "Hand-knotted wool, 8'-0\" x 10'-0\"", "#8A1E22")
    BRASS = Finish("MT-1", "Polished Brass", "Hardware, lamp fittings", "#B58E46")
    PORCELAIN = Finish("CR-1", "Blanc de Chine", "Glazed porcelain lamp bodies", "#F3F0EA")
    SHADE = Finish("LS-1", "Ivory Silk Shade", "Pleated silk lamp shades", "#EADCC0")
    TOLE = Finish("LS-2", "Red Tole", "Painted metal bouillotte shades, gilt band", "#6E1016")
    GLASS = Finish("GZ-1", "Clear Glass", "Window glazing", "#CFE3E8")
    MIRROR = Finish("GZ-2", "Mirror Glass", "Silvered mirror plate", "#C8CCCF")
    CRYSTAL = Finish("GZ-3", "Lead Crystal", "Chandelier prisms and beads", "#E8F1F4")
    WAX = Finish("LT-1", "Candle Sleeve", "Ivory resin candle sleeves", "#EFE6D2")
    BULB = Finish("LT-2", "Flame-tip Lamp", "2700K LED filament, dimmable", "#FFD9A0")
    WALL_SHELL = Finish("P-4", "Exterior Shell", "Hidden exterior face of walls", "#B9B2A6")


class Group(Enum):
    """Model category; the value is the AIA-style DXF layer used for the 3D export."""

    SHELL = "A-SHEL-3D"
    MILLWORK = "A-MILL-3D"
    OPENINGS = "A-OPNG-3D"
    CEILING = "A-CLNG-3D"
    FURNITURE = "I-FURN-3D"
    SOFT_GOODS = "I-SOFT-3D"
    LIGHTING = "E-LITE-3D"
    ACCESSORIES = "I-ACCS-3D"


class Shading(Enum):
    """How the renderer treats a part's surface."""

    FLAT = "flat"  # architectural planes
    CRISP = "crisp"  # smooth-by-angle, sharp edges kept (moldings, turnings)
    EASED = "eased"  # small bevel on every edge (casework, frames)
    SOFT = "soft"  # subdivision surface (cushions, pillows, fabric)


@dataclass(frozen=True)
class Part:
    name: str
    mesh: Mesh
    mat: Mat
    group: Group
    shading: Shading


@dataclass(frozen=True)
class Lamp:
    """A light source inside a fixture (position in inches, radiometric watts for Cycles)."""

    name: str
    position: tuple[float, float, float]
    watts: float
    radius: float
    color: tuple[float, float, float]


WARM_2700K = (1.0, 0.72, 0.42)
CANDLE_2200K = (1.0, 0.62, 0.3)
