"""Words for the review document (everything numeric comes from spec.py)."""

CONCEPT = (
    "A bedroom in Pompeian red, written in the neoclassical language of the late eighteenth century. "
    "The colour is the one excavated on the walls of Pompeii and Herculaneum; the treatment is the one "
    "Robert Adam and the Louis XVI cabinetmakers gave it &mdash; ivory panelling, gilt ornament, black "
    "lacquer and marble, all held in strict symmetry."
)
PLAN_IDEA = (
    "The room is planned on one axis. The bed stands centred on the west wall beneath a half-tester canopy "
    "and faces the door; the four windows are set in matched pairs on the two long walls, so daylight falls "
    "evenly on both sides of the bed. Every element has its mirror: nightstands, lamps, sconces, commodes, "
    "oval glasses and drapery."
)
DESIGN_MOVES = (
    ("Walls", "Pompeian-red walls above an ivory panelled dado; applied ivory moldings frame every bay."),
    ("Ceiling", "Dentil cornice, a gilt Greek-key border, and an Adam-style ring, medallion and corner fans."),
    ("The bed", "A Louis XVI <i>lit &agrave; la duchesse</i> under a gilt half-tester with a scalloped crimson "
                "valance, champagne silk curtains and a red silk-damask backdrop."),
    ("Case pieces", "Ebonized commodes and nightstands with gilt mounts and white marble: the black, red and "
                    "gold of the Pompeian frescoes."),
    ("Floor", "Herringbone oak under an Aubusson-style rug with a laurel medallion and Greek-key border."),
    ("Light", "Crystal basket chandelier, candle sconces, porcelain bedside lamps and bouillotte lamps, all "
              "dimmable at 2200&ndash;2700&thinsp;K."),
)
CAPTIONS = {
    "hero": ("View from the door", "The axial view: canopy bed, matched windows and sconces, chandelier on the "
                                    "room's centre point."),
    "bed": ("The bed wall", "Half-tester with scalloped valance and bullion fringe; ebonized nightstands with "
                            "marble tops and pierced brass galleries."),
    "canopy": ("Under the canopy", "Damask shams, garnet velvet bolster with gilt tassels, and the laurel-and-ribbon "
                                   "crest on the headboard."),
    "door_wall": ("Toward the door", "Fluted-pilaster doorcase between twin commodes, oval glasses and red-tole "
                                     "bouillotte lamps."),
    "evening": ("After dark", "Candle-light at 2200&thinsp;K: chandelier, sconces and lamps on dimmers."),
    "plan": ("Rendered plan", "Ceiling removed. Bed on the axis, rug under the foot of the bed, matched case "
                              "pieces either side of the door."),
}
ASSUMPTIONS = (
    "Window positions are a design choice: two on each 16'-0\" wall, 4'-8\" from the corners and 6'-8\" on "
    "centre. If your windows sit elsewhere, the model is parametric and everything regenerates.",
    "Door: one 36\" door centred on the east wall. No closet is shown inside the 16' x 12' footprint.",
    "Bed: queen. A king fits only with 18\" nightstands, or with the bed moved to a long wall.",
    "Wall thicknesses (6&frac12;\" exterior, 4&frac12;\" interior) and the 6'-8\" head height are assumed.",
    "Colours are given as sRGB values; approve physical paint and fabric samples before ordering.",
)
QUESTIONS = (
    "Is the axial layout (bed facing the door) right for you, or would you rather the bed faced the windows?",
    "Walls: keep this Pompeian red, or go deeper (oxblood) or softer (Etruscan coral)?",
    "Canopy curtains in champagne silk, or crimson to match the windows?",
)
HOW_TO_OPEN = (
    ("AutoCAD / AutoCAD LT", "Open <b>Pompeian_Bedroom_Drawings.dxf</b> directly. Seven layout tabs (A-001 to "
                             "A-501) are set up as 17 x 11 sheets with scaled viewports. SAVEAS converts to DWG."),
    ("AutoCAD 3D", "<b>Pompeian_Bedroom_3D_Model.dxf</b>: every object is a MESH on a layer per category and "
                   "finish (e.g. I-FURN-3D-GL-1), in inches. Use any 3D view with the Realistic visual style."),
    ("3ds Max / Maya", "Import <b>Pompeian_Bedroom_3D.fbx</b> (real-world units, objects grouped by category)."),
    ("Revit", "Insert &rarr; Link CAD with the DXF set for plans and elevations. Use the 3D DXF or OBJ as a "
              "massing reference."),
    ("Fusion / others", "<b>Pompeian_Bedroom_3D.obj</b> + .mtl, in inches, matching the drawings."),
)
