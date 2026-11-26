"""DXF scaffolding: units, AIA layers, text/dimension styles and annotation helpers."""

import math
from dataclasses import dataclass
from enum import Enum

import ezdxf
from ezdxf.enums import TextEntityAlignment
from ezdxf.layouts import BaseLayout

TEXT_STYLE = "ARCH"
DIM_STYLE = "ARCH-TICK"
PAPER_TEXT = 3.0 / 32.0  # notes on paper (inches)


@dataclass(frozen=True)
class LayerDef:
    name: str
    color: int  # AutoCAD Color Index
    lineweight: int  # 1/100 mm
    linetype: str
    plot: bool


class Layer(Enum):
    WALL = LayerDef("A-WALL", 7, 50, "Continuous", True)
    WALL_PATT = LayerDef("A-WALL-PATT", 8, 0, "Continuous", True)
    DOOR = LayerDef("A-DOOR", 7, 25, "Continuous", True)
    GLAZ = LayerDef("A-GLAZ", 7, 18, "Continuous", True)
    MILL = LayerDef("A-MILL", 7, 18, "Continuous", True)
    FLOR_PATT = LayerDef("A-FLOR-PATT", 9, 9, "Continuous", True)
    FURN = LayerDef("I-FURN", 7, 18, "Continuous", True)
    FURN_OVHD = LayerDef("I-FURN-OVHD", 8, 13, "DASHED", True)
    SOFT = LayerDef("I-SOFT", 7, 13, "Continuous", True)
    CLNG = LayerDef("A-CLNG", 7, 18, "Continuous", True)
    CLNG_ORNM = LayerDef("A-CLNG-ORNM", 8, 13, "Continuous", True)
    LITE = LayerDef("E-LITE", 7, 25, "Continuous", True)
    POWR = LayerDef("E-POWR", 7, 18, "Continuous", True)
    CIRC = LayerDef("E-LITE-CIRC", 8, 13, "DASHED", True)
    ELEV = LayerDef("A-ELEV", 7, 25, "Continuous", True)
    ELEV_FINE = LayerDef("A-ELEV-FINE", 7, 13, "Continuous", True)
    ELEV_FURN = LayerDef("A-ELEV-FURN", 8, 13, "Continuous", True)
    ELEV_PATT = LayerDef("A-ELEV-PATT", 9, 0, "Continuous", True)
    DETL = LayerDef("A-DETL", 7, 35, "Continuous", True)
    DETL_PATT = LayerDef("A-DETL-PATT", 8, 9, "Continuous", True)
    DIMS = LayerDef("A-ANNO-DIMS", 7, 13, "Continuous", True)
    TEXT = LayerDef("A-ANNO-TEXT", 7, 18, "Continuous", True)
    SYMB = LayerDef("A-ANNO-SYMB", 7, 18, "Continuous", True)
    TTLB = LayerDef("A-ANNO-TTLB", 7, 35, "Continuous", True)
    NPLT = LayerDef("A-ANNO-NPLT", 8, 13, "Continuous", False)
    MESH3D = LayerDef("A-3D-MODEL", 7, 13, "Continuous", True)


def new_document() -> ezdxf.document.Drawing:
    doc = ezdxf.new("R2018", setup=True, units=ezdxf.units.IN)
    doc.header["$LUNITS"] = 4  # architectural
    doc.header["$INSUNITS"] = 1
    doc.header["$MEASUREMENT"] = 0
    doc.header["$LTSCALE"] = 1.0
    doc.header["$PSLTSCALE"] = 1
    doc.styles.new(TEXT_STYLE, dxfattribs={"font": "arial.ttf"})
    for layer in Layer:
        d = layer.value
        entry = doc.layers.add(d.name, color=d.color, linetype=d.linetype)
        entry.dxf.lineweight = d.lineweight
        entry.dxf.plot = int(d.plot)
    style = doc.dimstyles.new(DIM_STYLE)
    style.dxf.dimtxsty = TEXT_STYLE
    style.dxf.dimtxt = PAPER_TEXT
    style.dxf.dimasz = PAPER_TEXT
    style.dxf.dimtsz = PAPER_TEXT * 0.8  # architectural tick
    style.dxf.dimexo = 1.0 / 16.0
    style.dxf.dimexe = 1.0 / 16.0
    style.dxf.dimgap = 1.0 / 32.0
    style.dxf.dimtad = 1
    style.dxf.dimtih = 0
    style.dxf.dimtoh = 0
    style.dxf.dimlunit = 4
    style.dxf.dimdec = 3
    style.dxf.dimclrd = 256
    style.dxf.dimclre = 256
    return doc


def attrs(layer: Layer) -> dict:
    return {"layer": layer.value.name}


def ft_in(inches: float) -> str:
    """Architectural length text: 16'-0", 2'-8", 7 1/4"."""
    eighths = int(round(inches * 8))
    feet, rem = divmod(eighths, 96)
    whole, frac = divmod(rem, 8)
    frac_txt = ("", " 1/8", " 1/4", " 3/8", " 1/2", " 5/8", " 3/4", " 7/8")[frac]
    inch_txt = f"{whole}{frac_txt}" if whole or not frac else frac_txt.strip()
    return f"{feet}'-{inch_txt}\"" if feet else f"{inch_txt}\""


class Canvas:
    """Draws into a layout with a fixed origin and annotation scale (model units per paper inch)."""

    def __init__(self, space: BaseLayout, origin: tuple[float, float], scale: float):
        self.space = space
        self.ox, self.oy = origin
        self.scale = scale

    def p(self, pt) -> tuple[float, float]:
        return (self.ox + float(pt[0]), self.oy + float(pt[1]))

    def poly(self, pts, layer: Layer, closed: bool) -> None:
        self.space.add_lwpolyline([self.p(q) for q in pts], close=closed, dxfattribs=attrs(layer))

    def rect(self, x0, y0, x1, y1, layer: Layer) -> None:
        self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer, closed=True)

    def line(self, a, b, layer: Layer) -> None:
        self.space.add_line(self.p(a), self.p(b), dxfattribs=attrs(layer))

    def circle(self, c, r: float, layer: Layer) -> None:
        self.space.add_circle(self.p(c), r, dxfattribs=attrs(layer))

    def arc(self, c, r: float, a0: float, a1: float, layer: Layer) -> None:
        self.space.add_arc(self.p(c), r, a0, a1, dxfattribs=attrs(layer))

    def text(self, s: str, at, paper_height: float, layer: Layer, align: TextEntityAlignment) -> None:
        t = self.space.add_text(s, height=paper_height * self.scale,
                                dxfattribs={**attrs(layer), "style": TEXT_STYLE})
        t.set_placement(self.p(at), align=align)

    def mtext(self, s: str, at, paper_height: float, paper_width: float, layer: Layer) -> None:
        m = self.space.add_mtext(s, dxfattribs={**attrs(layer), "style": TEXT_STYLE,
                                                "char_height": paper_height * self.scale,
                                                "width": paper_width * self.scale})
        m.set_location(self.p(at), attachment_point=1)

    def _hatch(self, loops: list, layer: Layer, color: int):
        hatch = self.space.add_hatch(color=color, dxfattribs=attrs(layer))
        for i, loop in enumerate(loops):
            hatch.paths.add_polyline_path([self.p(q) for q in loop], is_closed=True, flags=1 if i == 0 else 16)
        return hatch

    def solid(self, loops: list, layer: Layer, color: int) -> None:
        self._hatch(loops, layer, color)

    def pattern(self, loops: list, layer: Layer, name: str, scale: float, angle: float) -> None:
        self._hatch(loops, layer, 256).set_pattern_fill(name, scale=scale, angle=angle)

    def dim(self, p1, p2, offset_paper: float, vertical: bool) -> None:
        """Dimension p1-p2; the dimension line sits offset_paper inches (on paper) away."""
        off = offset_paper * self.scale
        mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
        base = (mid[0] + off, mid[1]) if vertical else (mid[0], mid[1] + off)
        length = abs(p2[1] - p1[1]) if vertical else abs(p2[0] - p1[0])
        dim = self.space.add_linear_dim(base=self.p(base), p1=self.p(p1), p2=self.p(p2),
                                        angle=90.0 if vertical else 0.0, dimstyle=DIM_STYLE, text=ft_in(length),
                                        override={"dimscale": self.scale}, dxfattribs=attrs(Layer.DIMS))
        dim.render()

    def circle_tag(self, label: str, at, paper_radius: float, layer: Layer) -> None:
        self.circle(at, paper_radius * self.scale, layer)
        self.text(label, at, paper_radius * 0.8, layer, TextEntityAlignment.MIDDLE_CENTER)

    def polygon_tag(self, label: str, at, paper_radius: float, sides: int, layer: Layer) -> None:
        r = paper_radius * self.scale
        pts = [(at[0] + r * math.cos(math.pi / sides + 2 * math.pi * k / sides),
                at[1] + r * math.sin(math.pi / sides + 2 * math.pi * k / sides)) for k in range(sides)]
        self.poly(pts, layer, closed=True)
        self.text(label, at, paper_radius * 0.72, layer, TextEntityAlignment.MIDDLE_CENTER)

    def lines(self, coords_list, layer: Layer) -> None:
        for c in coords_list:
            self.poly(c, layer, closed=False)
