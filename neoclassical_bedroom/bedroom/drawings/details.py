"""A-501 millwork profile details and the schedules / notes tables (paper space)."""

from ezdxf.enums import TextEntityAlignment as TA

import textwrap

import numpy as np

from ..model.ceiling import KEY_HOOK, KEY_UNIT
from ..model.openings import fluted_section
from ..model.parts import Mat
from ..model.profiles import DETAILED_PROFILES
from ..spec import FIXTURES, FURNITURE, OPENINGS, PILASTER_PROJ, PILASTER_W, PROJECT, OpeningKind
from .cad import Canvas, Layer, ft_in


KEY_DETAIL_FACTOR = 0.5


def _key_detail() -> list[np.ndarray]:
    """Three periods of the ceiling Greek key with its fillet lines, as plan polylines."""
    unit = KEY_UNIT * KEY_DETAIL_FACTOR
    hooks = [KEY_HOOK * unit + [4 * unit * k, 0.0] for k in range(2)]
    lines = [np.array([[-0.5 * unit, y], [8.5 * unit, y]]) for y in (-unit, 5 * unit)]
    return hooks + lines


def _detail_cell(c: Canvas, title: str, note: str, shape: np.ndarray, at: tuple[float, float]) -> None:
    pts = shape + np.asarray(at) - [shape[:, 0].min(), 0.0]
    c.pattern([pts], Layer.DETL_PATT, "ANSI31", 0.25, 0.0)
    c.poly(pts, Layer.DETL, closed=True)
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    c.dim((lo[0], hi[1]), (hi[0], hi[1]), 0.3, vertical=False)
    c.dim((hi[0], lo[1]), (hi[0], hi[1]), 0.35, vertical=True)
    c.text(title, (lo[0], lo[1] - 0.95), 0.11, Layer.TEXT, TA.LEFT)
    c.text(note, (lo[0], lo[1] - 1.4), 0.07, Layer.TEXT, TA.LEFT)


def profile_details(c: Canvas, scale_label: str) -> None:
    """Molding sections at full size in model space on a 4-column grid; viewport sets the scale."""
    note = f"PAINT-GRADE POPLAR, P-2  |  SCALE: {scale_label}"
    shapes = [(t, p) for t, p in DETAILED_PROFILES] + [("DOORCASE PILASTER (PLAN)", fluted_section(0.0, PILASTER_W,
                                                                                                    PILASTER_PROJ, 5))]
    for i, (title, shape) in enumerate(shapes):
        col, row = i % 4, i // 4
        _detail_cell(c, title, note, shape, (col * 6.6, -row * 5.2))
    origin = np.array([3 * 6.6, -5.2 + KEY_UNIT * KEY_DETAIL_FACTOR])
    for path in _key_detail():
        c.poly(path + origin, Layer.DETL, closed=False)
    c.text("CEILING GREEK-KEY BORDER", (origin[0], -5.2 - 0.95), 0.11, Layer.TEXT, TA.LEFT)
    c.text("GL-1 GILT RELIEF ON 1.1\" GRID  |  SHOWN AT HALF DETAIL SCALE", (origin[0], -5.2 - 1.4), 0.07,
           Layer.TEXT, TA.LEFT)


def table(c: Canvas, at: tuple[float, float], title: str, widths: list[float], rows: list[tuple]) -> float:
    """Simple ruled table in paper space; returns the bottom y."""
    x0, y = at
    row_h, pad = 0.2, 0.05
    c.text(title, (x0, y + 0.08), 0.12, Layer.TEXT, TA.LEFT)
    width = sum(widths)
    for r, row in enumerate(rows):
        c.line((x0, y), (x0 + width, y), Layer.TTLB if r == 0 else Layer.TEXT)
        x = x0
        for w, cell in zip(widths, row):
            c.text(str(cell), (x + pad, y - row_h / 2), 0.08 if r else 0.075, Layer.TEXT, TA.MIDDLE_LEFT)
            x += w
        y -= row_h
    c.line((x0, y), (x0 + width, y), Layer.TTLB)
    for k in range(len(widths) + 1):
        xk = x0 + sum(widths[:k])
        c.line((xk, at[1]), (xk, y), Layer.TEXT)
    return y


def opening_rows() -> list[tuple]:
    rows = [("TAG", "TYPE", "WIDTH", "HEIGHT", "SILL", "HEAD", "WALL", "REMARKS")]
    for o in OPENINGS:
        kind = "6/6 DOUBLE-HUNG" if o.kind is OpeningKind.WINDOW else "6-PANEL SWING"
        remark = ("CASED, STOOL & APRON, HEAD CAP; DRAPERY D-1" if o.kind is OpeningKind.WINDOW
                  else "FLUTED PILASTER DOORCASE, BRASS KNOB")
        rows.append((o.tag, kind, ft_in(o.width), ft_in(o.top - o.bottom), ft_in(o.bottom), ft_in(o.top),
                     o.wall.value.label.upper(), remark))
    return rows


def finish_rows() -> list[tuple]:
    rows = [("CODE", "FINISH", "DESCRIPTION", "COLOR (sRGB)")]
    rows += [(m.value.code, m.value.name.upper(), m.value.description, m.value.hex_color.upper())
             for m in Mat if m is not Mat.WALL_SHELL]
    return rows


def ffe_rows() -> list[tuple]:
    rows = [("TAG", "ITEM", "SIZE W x D x H", "QTY", "FINISHES")]
    for item in FURNITURE + FIXTURES:
        w, d, h = item.size
        rows.append((item.tag, item.name.upper(), f"{ft_in(w)} x {ft_in(d)} x {ft_in(h)}", len(item.placements),
                     ", ".join(item.finishes)))
    return rows


GENERAL_NOTES = """GENERAL NOTES
1. DIMENSIONS ARE TO FINISHED INTERIOR FACES UNLESS NOTED. ALL DIMENSIONS IN FEET-INCHES. DRAWING UNIT = 1 INCH.
2. ROOM: 16'-0" x 12'-0" CLEAR, 8'-0" FINISHED CEILING. FOUR WINDOWS 2'-8" x 4'-3" (UNIT SIZE), HEADS AT 6'-8" AFF.
3. WINDOW AND DOOR HEADS ALIGN AT 6'-8" AFF; CHAIR RAIL TOP ALIGNS WITH WINDOW STOOLS AT 2'-6" AFF.
4. ALL MILLWORK PAINT-GRADE POPLAR / MDF, PRIMED, TWO COATS P-2 SATIN ENAMEL. GILDING GL-1 BY SPECIALIST.
5. WALL OPENING LOCATIONS AND WALL THICKNESSES ARE DESIGN ASSUMPTIONS - FIELD VERIFY BEFORE FABRICATION.
6. CEILING MEDALLION, RING, FANS AND GREEK-KEY BORDER: CAST PLASTER OR POLYURETHANE, ADHERED AND PINNED.
7. PROVIDE BLOCKING FOR CANOPY (F-2), DRAPERY POLES, MIRRORS (F-6) AND SCONCES (L-2). CHANDELIER BOX RATED 50 LB.
8. ELECTRICAL LAYOUT IS DESIGN INTENT ONLY; FINAL CIRCUITING BY LICENSED ELECTRICIAN TO LOCAL CODE.
9. 3D MODEL, RENDERINGS AND THIS SET ARE GENERATED FROM ONE PARAMETRIC SOURCE (SEE README)."""


def schedules(c: Canvas) -> None:
    """Cover-sheet content: notes, schedules (paper space, inches)."""
    c.text(PROJECT.upper(), (0.6, 10.15), 0.3, Layer.TTLB, TA.LEFT)
    c.text("NEOCLASSICAL BEDROOM  -  DESIGN DEVELOPMENT SET  -  FOR REVIEW", (0.62, 9.82), 0.12, Layer.TEXT, TA.LEFT)
    lines = [w for note in GENERAL_NOTES.splitlines() for w in textwrap.wrap(note, 112, subsequent_indent="   ")]
    for i, ln in enumerate(lines):
        c.text(ln, (0.6, 9.45 - i * 0.135), 0.072, Layer.TEXT, TA.LEFT)
    y = table(c, (0.6, 7.25), "WINDOW & DOOR SCHEDULE", [0.4, 1.15, 0.55, 0.55, 0.5, 0.5, 0.55, 2.75], opening_rows())
    table(c, (0.6, y - 0.45), "FINISH SCHEDULE", [0.45, 1.5, 3.65, 1.0], finish_rows())
    table(c, (8.0, 9.4), "FURNITURE, FIXTURES & EQUIPMENT", [0.45, 2.25, 1.75, 0.35, 1.35], ffe_rows())


def lighting_legend(c: Canvas, at: tuple[float, float]) -> None:
    x, y = at
    c.text("LIGHTING & POWER LEGEND", (x, y), 0.11, Layer.TEXT, TA.LEFT)
    entries = [("L-1", "CRYSTAL BASKET CHANDELIER, 6 x 2700K FLAME-TIP LED, DIMMED"),
               ("L-2", "TWO-ARM GILT SCONCE, 2 x 2700K, DIMMED, CENTER 4'-10\" AFF"),
               ("S3D", "3-WAY DIMMER (DOOR + BEDSIDE) - CHANDELIER"),
               ("SD", "DIMMER - SCONCES"),
               ("S", "SWITCH - COMMODE LAMP RECEPTACLES"),
               ("(=)", "DUPLEX RECEPTACLE 12\" AFF; HALF-SHADED = SWITCHED")]
    for i, (sym, desc) in enumerate(entries):
        c.text(sym, (x, y - 0.25 - i * 0.2), 0.08, Layer.TEXT, TA.LEFT)
        c.text(desc, (x + 0.45, y - 0.25 - i * 0.2), 0.075, Layer.TEXT, TA.LEFT)
