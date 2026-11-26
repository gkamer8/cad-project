# The Pompeian Bedroom

A neoclassical bedroom in Pompeian red: 16'-0" x 12'-0", 8'-0" ceiling, four 32" x 51" windows.
One parametric source (`bedroom/spec.py`) drives the 3D model, the photoreal renderings, the
AutoCAD drawing set and the review PDF, so they always agree.

## Deliverables

| File | Open with | What it is |
|---|---|---|
| `output/Pompeian_Bedroom_Design_Review.pdf` | any PDF viewer | Review book: renderings, concept, specifications, schedules, then the full drawing set |
| `output/cad/Pompeian_Bedroom_Drawings.dxf` | AutoCAD, AutoCAD LT, Revit (Link CAD), DraftSight | 2D drawing set, 8 paper-space sheets (17 x 11) with title blocks and scaled viewports |
| `output/cad/Pompeian_Bedroom_3D_Model.dxf` | AutoCAD | Full 3D model as MESH entities, one layer per category + finish, inches |
| `output/cad/Pompeian_Bedroom_3D.fbx` | 3ds Max, Maya, Autodesk Viewer | 3D model with materials (real-world units) |
| `output/cad/Pompeian_Bedroom_3D.obj` (+ `.mtl`) | Fusion, Revit (as reference), most 3D tools | 3D model in inches |
| `output/cad/Pompeian_Bedroom_Drawing_Set.pdf` | any PDF viewer | Vector plot of the 8 sheets |
| `output/renders/*.png` | any image viewer | 1920 px Cycles renderings |
| `output/sheets/*.png` | any image viewer | Quick previews of each drawing sheet |

DWG: the DXF files open directly in AutoCAD (File > Open > DXF); use SAVEAS to keep a DWG copy.

### Drawing set

| Sheet | Title | Scale |
|---|---|---|
| A-001 | Cover, notes & schedules (windows/doors, finishes, FF&E) | - |
| A-101 | Floor plan & furniture layout | 1/2" = 1'-0" |
| A-102 | Reflected ceiling, lighting & power | 1/2" = 1'-0" |
| A-201 | Interior elevation, north | 1/2" = 1'-0" |
| A-202 | Interior elevation, south | 1/2" = 1'-0" |
| A-203 | Interior elevation, east (door wall) | 3/4" = 1'-0" |
| A-204 | Interior elevation, west (bed wall) | 3/4" = 1'-0" |
| A-501 | Millwork profile details | 6" = 1'-0" |

Layers follow AIA-style names (`A-WALL`, `A-GLAZ`, `I-FURN`, `E-LITE`, `A-ANNO-DIMS`, ...). Furniture
linework in plans and elevations is traced from the 3D model with hidden-line removal.

## Design summary

- Bed on the axis of the room, centred on the west wall under a half-tester canopy, facing the door.
- Windows in matched pairs on the two long walls (4'-8" from the corners, 6'-8" on centre), heads at
  6'-8", sills at 2'-5"; door centred on the east wall in a fluted-pilaster doorcase.
- Pompeian-red walls over an ivory panelled dado, dentil cornice, gilt Greek-key ceiling border,
  Adam-style ring, medallion and corner fans; herringbone oak floor with an Aubusson-style rug.
- Ebonized commodes and nightstands with gilt mounts and white marble; crystal basket chandelier,
  candle sconces and bouillotte lamps at 2200-2700 K.

Assumptions to confirm: window and door locations, queen bed, wall thicknesses (6 1/2" exterior,
4 1/2" interior). Change them in `bedroom/spec.py` and rebuild.

## Rebuilding

Python 3.11 with `pip install -r requirements.txt`, plus Node with Playwright/Chromium for the PDF.

```sh
PY=/path/to/python3.11 ./build_all.sh
```

`build_all.sh` fetches the CC0 textures/HDRI (Poly Haven) and OFL fonts into `assets/`, renders the
six views (about 15 minutes each on 4 CPU cores), builds the DXF/PDF drawing set, exports FBX/OBJ and
assembles the review PDF. Each step can also be run on its own; see the scripts' docstrings.

## Code layout

```
bedroom/spec.py          room, openings, heights, furniture placements (single source of truth)
bedroom/geom/            numpy mesh kernel: sweeps with true mitres, lathes, lofts, tubes, soft shapes
bedroom/model/           architecture, millwork, ceiling, openings, bed + canopy, case goods, lighting, drapery
bedroom/render/          Blender/Cycles materials, scene, cameras and lighting moods
bedroom/drawings/        ezdxf drawing set: plans, RCP, elevations, details, sheets, hidden-line silhouettes
bedroom/report/          review-book HTML (printed by tools/print_pdf.cjs)
bedroom/textures/rug.py  procedural Aubusson-style rug artwork
```

Textures: Poly Haven (CC0). Fonts: Cormorant Garamond and Inter (SIL Open Font License).
