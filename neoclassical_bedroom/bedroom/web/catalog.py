"""What the web explorer knows about each object: assemblies, layers, finishes, lamps, views."""

from dataclasses import dataclass

from ..drawings.cad import ft_in
from ..model.parts import Group, Lamp, Mat, Part
from ..render.views import Shots
from ..spec import (BED, BEDSIDE_LAMP, BENCH, BOUILLOTTE, CANOPY, CEILING_H, CHANDELIER, COMMODE, MIRROR,
                    NIGHTSTAND, OPENINGS, ROOM_L, ROOM_W, RUG, SCONCE, Item, OpeningKind)

INCH = 0.0254


@dataclass(frozen=True)
class Assembly:
    """A thing a visitor would click on: one item, opening or architectural element."""

    key: str
    label: str
    tag: str
    kind: str
    description: str
    size: str
    prefixes: tuple[str, ...]


LAYER_LABELS = {
    Group.SHELL: "Walls, floor & ceiling",
    Group.MILLWORK: "Millwork & trim",
    Group.OPENINGS: "Windows & door",
    Group.CEILING: "Ceiling ornament",
    Group.FURNITURE: "Furniture",
    Group.SOFT_GOODS: "Textiles",
    Group.LIGHTING: "Lighting",
    Group.ACCESSORIES: "Accessories",
}


def _item(key: str, item: Item, prefixes: tuple[str, ...]) -> Assembly:
    w, d, h = item.size
    qty = f" (x{len(item.placements)})" if len(item.placements) > 1 else ""
    return Assembly(key, item.name, item.tag, "Furniture & fixtures", item.description,
                    f"{ft_in(w)} W x {ft_in(d)} D x {ft_in(h)} H{qty}", prefixes)


def _architecture(key: str, label: str, description: str, prefixes: tuple[str, ...]) -> Assembly:
    return Assembly(key, label, "", "Architecture", description, "", prefixes)


def assemblies() -> list[Assembly]:
    items = [
        _item("bed", BED, ("bed_frame", "bedding")),
        _item("canopy", CANOPY, ("canopy",)),
        _item("nightstands", NIGHTSTAND, ("nightstand",)),
        _item("bench", BENCH, ("bench",)),
        _item("commodes", COMMODE, ("commode",)),
        _item("mirrors", MIRROR, ("mirror",)),
        _item("rug", RUG, ("rug",)),
        _item("chandelier", CHANDELIER, ("chandelier",)),
        _item("sconces", SCONCE, ("sconce",)),
        _item("bedside_lamps", BEDSIDE_LAMP, ("bedside_lamp",)),
        _item("bouillottes", BOUILLOTTE, ("bouillotte",)),
        Assembly("urns", "Garniture urns (pair)", "", "Furniture & fixtures",
                 "Black-lacquer urns with gilt handles on the commodes.", "", ("urn",)),
        Assembly("drapery", "Window drapery (4 pairs)", "D-1", "Furniture & fixtures",
                 "Crimson silk panels on gilt poles with pinecone finials, held back with gilt cords and tassels.",
                 "", ("drapery",)),
    ]
    openings = [
        Assembly(o.tag.lower(), f"{o.kind.value} {o.tag}", o.tag, "Openings",
                 (f"6-over-6 double-hung, cased with stool, apron and head cap; {o.wall.value.label.lower()} wall."
                  if o.kind is OpeningKind.WINDOW else
                  "Six-panel door in a fluted-pilaster doorcase with gilt paterae; east wall."),
                 f"{ft_in(o.width)} W x {ft_in(o.top - o.bottom)} H, sill {ft_in(o.bottom)}, head {ft_in(o.top)}",
                 (f"{o.tag.lower()}_",))
        for o in OPENINGS
    ]
    architecture = [
        _architecture("walls", "Walls", "Pompeian-red upper walls over an ivory-painted dado.", ("wall_",)),
        _architecture("floor", "Floor", "White-oak herringbone parquet.", ("floor",)),
        _architecture("ceiling", "Ceiling", "Flat plaster ceiling at 8'-0\".", ("ceiling",)),
        _architecture("ceiling_ornament", "Ceiling ornament",
                      "Panel molding, gilt Greek-key border, central ring, medallion and quarter fans.",
                      ("ceiling_moldings", "ceiling_medallion", "ceiling_gilt")),
        _architecture("cornice", "Dentil cornice", "4 1/2\" crown over a dentil course and astragal.", ("cornice",)),
        _architecture("baseboard", "Baseboard", "7 1/4\" painted baseboard with shoe and cyma cap.", ("baseboard",)),
        _architecture("chair_rail", "Chair rail", "Top at 2'-6\", aligned with the window stools.", ("chair_rail",)),
        _architecture("panels", "Applied wall panels", "Picture-frame moldings on every wall bay, dado and upper.",
                      ("panel_moldings",)),
        _architecture("damask", "Damask bed-wall panel", "Red silk damask upholstered panel with a gilt bead.",
                      ("damask",)),
    ]
    return items + openings + architecture


def _views() -> list[dict]:
    """Camera bookmarks matching the renderings (glTF coordinates: x east, y up, z south)."""
    out = []
    for shot in Shots:
        v = shot.value.view
        ex, ey, ez = v.eye
        out.append({"key": v.name, "eye": [ex * INCH, ez * INCH, -ey * INCH],
                    "target": [v.look_at[0] * INCH, ez * INCH, -v.look_at[1] * INCH],
                    "fov_mm": v.lens_mm, "plan": v.pitch_deg > 45.0})
    return out


def catalog(parts: list[Part], lamps: list[Lamp]) -> dict:
    by_assembly = {}
    for a in assemblies():
        names = [p.name for p in parts if p.name.startswith(a.prefixes)]
        by_assembly[a.key] = {"label": a.label, "tag": a.tag, "kind": a.kind, "description": a.description,
                              "size": a.size, "parts": names}
    claimed = {n for a in by_assembly.values() for n in a["parts"]}
    orphans = [p.name for p in parts if p.name not in claimed]
    assert not orphans, f"parts without an assembly: {orphans}"
    return {
        "room": {"length_in": ROOM_L, "width_in": ROOM_W, "height_in": CEILING_H},
        "assemblies": by_assembly,
        "parts": {p.name: {"layer": p.group.value, "finish": p.mat.value.code} for p in parts},
        "layers": [{"key": g.value, "label": LAYER_LABELS[g]} for g in Group],
        "finishes": {m.value.code: {"name": m.value.name, "description": m.value.description,
                                    "hex": m.value.hex_color} for m in Mat},
        "lamps": [{"position": [l.position[0] * INCH, l.position[2] * INCH, -l.position[1] * INCH],
                   "watts": l.watts, "color": list(l.color)} for l in lamps],
        "views": _views(),
    }
