"""DXF/PDF outputs: the 3D mesh model for AutoCAD and vector PDFs of the paper sheets."""

from pathlib import Path

import ezdxf
import pymupdf
from ezdxf.addons.drawing import Frontend, RenderContext, config, layout
from ezdxf.addons.drawing import pymupdf as pdf_backend
from ezdxf.math import BoundingBox2d

from ..model.parts import Part


def _true_color(hex_color: str) -> int:
    return int(hex_color.lstrip("#"), 16)


def write_model_dxf(parts: list[Part], path: Path) -> None:
    """Every part as an AutoCAD MESH on a layer per category + finish (units: inches)."""
    doc = ezdxf.new("R2018", units=ezdxf.units.IN)
    msp = doc.modelspace()
    name = lambda part: f"{part.group.value}-{part.mat.value.code}"
    for group, mat in sorted({(p.group, p.mat) for p in parts}, key=lambda gm: (gm[0].value, gm[1].value.code)):
        entry = doc.layers.add(f"{group.value}-{mat.value.code}")
        entry.dxf.true_color = _true_color(mat.value.hex_color)
        entry.description = f"{mat.value.name}: {mat.value.description}"
    for part in parts:
        mesh = msp.add_mesh(dxfattribs={"layer": name(part)})
        with mesh.edit_data() as data:
            data.vertices = [tuple(v) for v in part.mesh.verts.tolist()]
            data.faces = [tuple(f) for f in (face.tolist() for face in part.mesh.faces())]
    doc.set_modelspace_vport(height=260, center=(96, 72))
    doc.saveas(path)


def sheets_to_pdf(doc: ezdxf.document.Drawing, path: Path, preview_dir: Path) -> list[Path]:
    """Vector PDF of every paper-space sheet (17 x 11 in) plus PNG previews; returns the previews."""
    cfg = config.Configuration(color_policy=config.ColorPolicy.MONOCHROME,
                               background_policy=config.BackgroundPolicy.WHITE,
                               lineweight_scaling=1.0, min_lineweight=0.12)
    book = pymupdf.open()
    previews = []
    preview_dir.mkdir(parents=True, exist_ok=True)
    sheets = sorted((lay for lay in doc.layouts if lay.is_any_paperspace), key=lambda lay: lay.dxf.taborder)
    for psp in sheets:
        name = psp.name
        backend = pdf_backend.PyMuPdfBackend()
        Frontend(RenderContext(doc), backend, config=cfg).draw_layout(psp, finalize=True)
        page = layout.Page(17.0, 11.0, layout.Units.inch)
        pdf = backend.get_pdf_bytes(page, settings=layout.Settings(fit_page=False, scale=25.4),
                                    render_box=BoundingBox2d([(0, 0), (17.0, 11.0)]))
        sheet = pymupdf.open("pdf", pdf)
        book.insert_pdf(sheet)
        out = preview_dir / f"{name.split()[0]}.png"
        sheet[0].get_pixmap(dpi=110).save(out)
        previews.append(out)
    book.save(path, garbage=3, deflate=True)
    return previews
