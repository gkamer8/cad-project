"""Build the showcase website into output/site (run with the bpy 4.5 interpreter).

    python build_site.py --gltf-transform /path/to/node_modules/.bin/gltf-transform

Needs the renders (render_views.py), the CAD set (build_cad.py, export_3d.py) and the review
book (build_report.py). The page is published as a claude.ai Artifact with output/site as root.
"""

import argparse
import base64
import json
import shutil
import subprocess
import sys
from pathlib import Path

import bpy
import numpy as np
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from bedroom.drawings.sheets import SHEETS  # noqa: E402
from bedroom.model.room import room_lamps, room_parts  # noqa: E402
from bedroom.paths import OUTPUT, RUG_IMAGE, TEXTURES  # noqa: E402
from bedroom.web.catalog import catalog  # noqa: E402
from bedroom.web.model_export import export_glb  # noqa: E402
from bedroom.web.page import DOWNLOADS, RENDER_ORDER, page  # noqa: E402

np.seterr(all="raise")
SITE = OUTPUT / "site"
CAD = OUTPUT / "cad"


def jpeg(src: Path, dest: Path, width: int, quality: int) -> None:
    img = Image.open(src).convert("RGB")
    img = img.resize((width, round(img.height * width / img.width)), Image.LANCZOS) if img.width > width else img
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, quality=quality, optimize=True, progressive=True)


def damask(dest: Path) -> None:
    """Recolour the grey jacquard into the red-on-red damask of finish FB-1."""
    lum = np.asarray(Image.open(TEXTURES / "floral_jacquard" / "diff.jpg").convert("L").resize((768, 1165)), float) / 255
    mask = np.clip((lum - 0.18) / 0.14, 0, 1)[..., None]
    ground, motif = np.array([94, 15, 20], float), np.array([156, 42, 46], float)
    Image.fromarray((ground + (motif - ground) * mask).astype(np.uint8)).save(dest, quality=86)


def model(gltf_transform: Path, work: Path) -> None:
    """The room as a meshopt-compressed GLB, published as base64 text (artifacts don't serve .glb)."""
    raw, glb = work / "raw.glb", work / "bedroom.glb"
    export_glb(room_parts(), raw)
    subprocess.run([str(gltf_transform), "optimize", str(raw), str(glb), "--compress", "meshopt", "--flatten", "false",
                    "--join", "false", "--instance", "false", "--palette", "false", "--simplify", "false",
                    "--texture-compress", "false"], check=True)
    out = SITE / "model" / "bedroom.glb.b64.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64encode(glb.read_bytes()))


def textures() -> None:
    tex = SITE / "tex"
    tex.mkdir(parents=True, exist_ok=True)
    jpeg(TEXTURES / "herringbone_parquet" / "diff.jpg", tex / "parquet.jpg", 1024, 84)
    jpeg(TEXTURES / "herringbone_parquet" / "nor_gl.jpg", tex / "parquet_normal.jpg", 1024, 90)
    jpeg(RUG_IMAGE, tex / "rug.jpg", 1600, 86)
    damask(tex / "damask.jpg")
    sky(tex / "garden.jpg")


def sky(dest: Path) -> None:
    """The HDR garden as an 8-bit equirectangular JPEG (the page can only serve web image types)."""
    img = bpy.data.images.load(str(TEXTURES / "hdri" / "borghese_gardens_4k.hdr"))
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    rgb = np.clip(px.reshape(h, w, 4)[::-1, :, :3] * 0.85, 0, 1)
    srgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(np.maximum(rgb, 0.0031308), 1 / 2.4) - 0.055)
    Image.fromarray((srgb * 255 + 0.5).astype(np.uint8)).resize((2048, 1024), Image.LANCZOS).save(
        dest, quality=86, optimize=True, progressive=True)


def images() -> None:
    for name in RENDER_ORDER:
        src = OUTPUT / "renders" / f"{name}.png"
        jpeg(src, SITE / "img" / "renders" / f"{name}.jpg", 1920, 84)
        jpeg(src, SITE / "img" / "renders" / "thumbs" / f"{name}.jpg", 960, 80)
    sheets_pdf = pymupdf.open(CAD / "Pompeian_Bedroom_Drawing_Set.pdf")
    (SITE / "img" / "sheets" / "thumbs").mkdir(parents=True, exist_ok=True)
    for sheet, pdf_page in zip(SHEETS, sheets_pdf):
        full = SITE / "img" / "sheets" / f"{sheet.number}.png"
        pdf_page.get_pixmap(dpi=150, colorspace=pymupdf.csGRAY).save(full)
        thumb = Image.open(full)
        thumb.resize((720, round(thumb.height * 720 / thumb.width)), Image.LANCZOS).save(
            SITE / "img" / "sheets" / "thumbs" / f"{sheet.number}.png", optimize=True)


def downloads() -> dict[str, str]:
    """Files behind the download buttons, in types the page can serve (zips are built in the browser)."""
    dl = SITE / "dl"
    dl.mkdir(parents=True, exist_ok=True)
    shutil.copy(OUTPUT / "Pompeian_Bedroom_Design_Review.pdf", dl)
    shutil.copy(CAD / "Pompeian_Bedroom_Drawing_Set.pdf", dl)
    shutil.copy(CAD / "Pompeian_Bedroom_Drawings.dxf", dl / "Pompeian_Bedroom_Drawings.dxf.txt")
    shutil.copy(ROOT / "README.md", dl / "README.txt")
    (dl / "Pompeian_Bedroom_3D.fbx.b64.txt").write_bytes(base64.b64encode((CAD / "Pompeian_Bedroom_3D.fbx").read_bytes()))
    sizes = {}
    for d in DOWNLOADS:
        raw = sum((SITE / path).stat().st_size * (0.75 if enc == "base64" else 1.0) for path, _, enc in d.parts)
        sizes[d.filename] = f"{raw / 1e6:.1f} MB" + (" before zipping" if d.filename.endswith(".zip") else "")
    return sizes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gltf-transform", type=Path, required=True)
    args = parser.parse_args()
    if SITE.exists():
        shutil.rmtree(SITE)
    work = OUTPUT / "site_build"
    work.mkdir(parents=True, exist_ok=True)
    model(args.gltf_transform, work)
    (SITE / "data").mkdir(parents=True, exist_ok=True)
    (SITE / "data" / "catalog.json").write_text(json.dumps(catalog(room_parts(), room_lamps())))
    textures()
    images()
    sizes = downloads()
    shutil.copytree(ROOT / "web", SITE, dirs_exist_ok=True)
    (SITE / "index.html").write_text(page(sizes), encoding="utf-8")
    total = sum(f.stat().st_size for f in SITE.rglob("*") if f.is_file())
    print(f"site: {len(list(SITE.rglob('*.*')))} files, {total / 1e6:.1f} MB")


main()
