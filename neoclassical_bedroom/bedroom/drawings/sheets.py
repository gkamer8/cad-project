"""Assemble the drawing set: model-space drawings, 17x11 paper sheets, title blocks, viewports."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date

import ezdxf
from ezdxf.enums import TextEntityAlignment as TA

from ..model.parts import Part
from ..spec import PROJECT, ROOM_L, ROOM_W, Wall
from .cad import Canvas, Layer, new_document
from .details import lighting_legend, profile_details, schedules
from .elevations import elevation
from .plans import ceiling_plan, floor_plan

SHEET_W, SHEET_H = 17.0, 11.0
TITLE_X = 14.25
ISSUE_DATE = date(2026, 11, 26).strftime("%Y-%m-%d")


@dataclass(frozen=True)
class Drawing:
    origin: tuple[float, float]  # model-space origin of the drawing
    center: tuple[float, float]  # model point shown at the viewport centre (relative to origin)
    scale: float  # model inches per paper inch
    scale_label: str


@dataclass(frozen=True)
class Port:
    drawing: Drawing
    paper_center: tuple[float, float]
    paper_size: tuple[float, float]


@dataclass(frozen=True)
class Sheet:
    number: str
    title: str
    ports: tuple[Port, ...]
    notes: Callable[[Canvas], None]  # paper-space annotation for this sheet


PLAN = Drawing((0.0, 0.0), (ROOM_L / 2 + 4, ROOM_W / 2), 24.0, "1/2\" = 1'-0\"")
RCP = Drawing((0.0, -320.0), (ROOM_L / 2 + 4, ROOM_W / 2), 24.0, "1/2\" = 1'-0\"")
ELEV = {
    Wall.NORTH: Drawing((420.0, 0.0), (ROOM_L / 2 + 8, 38.0), 24.0, "1/2\" = 1'-0\""),
    Wall.SOUTH: Drawing((420.0, -200.0), (ROOM_L / 2 + 8, 38.0), 24.0, "1/2\" = 1'-0\""),
    Wall.EAST: Drawing((760.0, 0.0), (ROOM_W / 2 + 6, 40.0), 16.0, "3/4\" = 1'-0\""),
    Wall.WEST: Drawing((760.0, -200.0), (ROOM_W / 2 + 6, 40.0), 16.0, "3/4\" = 1'-0\""),
}
DETAILS = Drawing((1000.0, 0.0), (12.6, 0.7), 2.0, "6\" = 1'-0\"")
ELEV_NUMBERS = {Wall.NORTH: "1", Wall.SOUTH: "1", Wall.EAST: "1", Wall.WEST: "1"}
ELEV_SHEETS = {Wall.NORTH: "A-201", Wall.SOUTH: "A-202", Wall.EAST: "A-203", Wall.WEST: "A-204"}

def _title_block(c: Canvas, sheet: Sheet, index: int) -> None:
    c.rect(0.25, 0.25, SHEET_W - 0.25, SHEET_H - 0.25, Layer.TTLB)
    c.line((TITLE_X, 0.25), (TITLE_X, SHEET_H - 0.25), Layer.TTLB)
    x = TITLE_X + 0.15
    c.text(PROJECT.upper(), (x, 10.35), 0.125, Layer.TTLB, TA.LEFT)
    c.text("NEOCLASSICAL BEDROOM", (x, 10.08), 0.1, Layer.TEXT, TA.LEFT)
    c.text("16'-0\" x 12'-0\" | 8'-0\" CLG", (x, 9.88), 0.085, Layer.TEXT, TA.LEFT)
    for y in (9.65, 6.0, 3.2, 1.75):
        c.line((TITLE_X, y), (SHEET_W - 0.25, y), Layer.TTLB)
    c.mtext("DESIGN DEVELOPMENT\\PFOR REVIEW - NOT FOR\\PCONSTRUCTION", (x, 9.45), 0.085, 2.3, Layer.TEXT)
    c.text("PREPARED WITH CLAUDE CODE", (x, 8.6), 0.075, Layer.TEXT, TA.LEFT)
    c.text(f"ISSUED: {ISSUE_DATE}", (x, 8.4), 0.075, Layer.TEXT, TA.LEFT)
    c.text("REV 0 - ISSUED FOR REVIEW", (x, 8.2), 0.075, Layer.TEXT, TA.LEFT)
    c.text("UNITS: INCHES (ARCHITECTURAL)", (x, 8.0), 0.075, Layer.TEXT, TA.LEFT)
    c.text("SHEET INDEX", (x, 5.75), 0.09, Layer.TEXT, TA.LEFT)
    for i, s in enumerate(SHEETS):
        marker = ">" if i == index else " "
        c.text(f"{marker} {s.number}  {s.title[:32]}", (x, 5.5 - i * 0.19), 0.058, Layer.TEXT, TA.LEFT)
    c.mtext(sheet.title, (x, 3.0), 0.12, 2.3, Layer.TTLB)
    c.text(sheet.number, (x, 0.75), 0.42, Layer.TTLB, TA.LEFT)
    c.text(f"{index + 1} OF {len(SHEETS)}", (SHEET_W - 0.4, 0.55), 0.08, Layer.TEXT, TA.RIGHT)


def _north_arrow(c: Canvas, at: tuple[float, float]) -> None:
    x, y = at
    c.circle((x, y), 0.3, Layer.SYMB)
    c.solid([[(x, y + 0.42), (x - 0.12, y - 0.18), (x, y - 0.05)]], Layer.SYMB, 250)
    c.poly([(x, y + 0.42), (x + 0.12, y - 0.18), (x, y - 0.05)], Layer.SYMB, closed=True)
    c.text("N", (x, y + 0.55), 0.12, Layer.SYMB, TA.MIDDLE_CENTER)


def _drawing_title(c: Canvas, at: tuple[float, float], number: str, title: str, scale_label: str) -> None:
    x, y = at
    c.circle_tag(number, (x, y), 0.17, Layer.SYMB)
    c.line((x + 0.22, y - 0.05), (x + 3.6, y - 0.05), Layer.TTLB)
    c.text(title, (x + 0.25, y + 0.02), 0.13, Layer.TEXT, TA.LEFT)
    c.text(f"SCALE: {scale_label}", (x + 0.25, y - 0.2), 0.075, Layer.TEXT, TA.LEFT)


def _plan_notes(c: Canvas) -> None:
    _north_arrow(c, (13.4, 9.8))
    _drawing_title(c, (0.7, 0.75), "1", "FLOOR PLAN", PLAN.scale_label)


def _rcp_notes(c: Canvas) -> None:
    _drawing_title(c, (0.7, 0.75), "1", "REFLECTED CEILING PLAN", RCP.scale_label)
    lighting_legend(c, (6.3, 1.75))
    _north_arrow(c, (13.4, 9.6))


def _no_notes(c: Canvas) -> None:
    c.text("ELEVATIONS ARE DRAWN LOOKING AT EACH WALL FROM INSIDE THE ROOM.", (0.6, 0.45), 0.07, Layer.TEXT, TA.LEFT)


def _detail_notes(c: Canvas) -> None:
    _drawing_title(c, (0.7, 0.75), "1", "MOLDING PROFILES (TYPICAL)", DETAILS.scale_label)


SHEETS = (
    Sheet("A-001", "COVER, NOTES & SCHEDULES", (), schedules),
    Sheet("A-101", "FLOOR PLAN & FURNITURE LAYOUT", (Port(PLAN, (7.05, 5.55), (13.3, 10.0)),), _plan_notes),
    Sheet("A-102", "REFLECTED CEILING, LIGHTING & POWER", (Port(RCP, (6.2, 5.55), (11.6, 10.0)),), _rcp_notes),
    Sheet("A-201", "INTERIOR ELEVATION - NORTH", (Port(ELEV[Wall.NORTH], (7.05, 5.75), (13.3, 9.6)),), _no_notes),
    Sheet("A-202", "INTERIOR ELEVATION - SOUTH", (Port(ELEV[Wall.SOUTH], (7.05, 5.75), (13.3, 9.6)),), _no_notes),
    Sheet("A-203", "INTERIOR ELEVATION - EAST (DOOR WALL)", (Port(ELEV[Wall.EAST], (7.05, 5.75), (12.6, 9.6)),), _no_notes),
    Sheet("A-204", "INTERIOR ELEVATION - WEST (BED WALL)", (Port(ELEV[Wall.WEST], (7.05, 5.75), (12.6, 9.6)),), _no_notes),
    Sheet("A-501", "MILLWORK PROFILE DETAILS", (Port(DETAILS, (7.05, 5.8), (13.3, 8.5)),), _detail_notes),
)




def _viewport(psp, port: Port) -> None:
    d = port.drawing
    vp = psp.add_viewport(center=port.paper_center, size=port.paper_size,
                          view_center_point=(d.origin[0] + d.center[0], d.origin[1] + d.center[1]),
                          view_height=port.paper_size[1] * d.scale, dxfattribs={"layer": Layer.NPLT.value.name})
    vp.dxf.status = 2


def build_drawing_set(parts: list[Part]) -> ezdxf.document.Drawing:
    doc = new_document()
    msp = doc.modelspace()
    refs = {w: f"{ELEV_NUMBERS[w]}/{ELEV_SHEETS[w][2:]}" for w in Wall}
    floor_plan(Canvas(msp, PLAN.origin, PLAN.scale), parts, refs)
    ceiling_plan(Canvas(msp, RCP.origin, RCP.scale))
    titles = {Wall.NORTH: "NORTH ELEVATION", Wall.SOUTH: "SOUTH ELEVATION", Wall.EAST: "EAST ELEVATION (DOOR WALL)",
              Wall.WEST: "WEST ELEVATION (BED WALL)"}
    for wall, d in ELEV.items():
        elevation(Canvas(msp, d.origin, d.scale), wall, parts, titles[wall], ELEV_NUMBERS[wall], d.scale_label)
    profile_details(Canvas(msp, DETAILS.origin, DETAILS.scale), DETAILS.scale_label)
    for index, sheet in enumerate(SHEETS):
        psp = doc.layouts.new(f"{sheet.number} {sheet.title}".replace(",", ""))  # AutoCAD forbids commas
        psp.page_setup(size=(SHEET_W, SHEET_H), margins=(0, 0, 0, 0), units="inch", scale=1)
        paper = Canvas(psp, (0.0, 0.0), 1.0)
        for port in sheet.ports:
            _viewport(psp, port)
        _title_block(paper, sheet, index)
        sheet.notes(paper)
    doc.layouts.delete("Layout1")
    return doc
