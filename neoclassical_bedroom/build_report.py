"""Build the design-review PDF: designed pages (HTML -> Chromium) followed by the CAD sheets.

    python build_report.py --renders output/renders --cad output/cad --out output

Needs the renders (render_views.py) and the CAD set (build_cad.py) to exist first.
"""

import argparse
import subprocess
import sys
from pathlib import Path

import pymupdf
from PIL import Image
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bedroom.drawings.sheets import SHEETS  # noqa: E402
from bedroom.paths import FONTS_CSS  # noqa: E402
from bedroom.report.document import document  # noqa: E402
from bedroom.spec import PROJECT  # noqa: E402

SHOTS = ("hero", "bed", "canopy", "door_wall", "evening", "plan")
HERE = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--renders", type=Path, required=True)
    parser.add_argument("--cad", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--previews", type=Path, required=True)
    args = parser.parse_args()
    work = (args.out / "report").resolve()
    (work / "img").mkdir(parents=True, exist_ok=True)
    images = {}
    for shot in SHOTS:
        jpg = work / "img" / f"{shot}.jpg"
        Image.open(args.renders / f"{shot}.png").convert("RGB").save(jpg, quality=90, optimize=True, progressive=True)
        images[shot] = jpg
    html = work / "review.html"
    html.write_text(document(images, FONTS_CSS, [(s.number, s.title.title()) for s in SHEETS]), encoding="utf-8")
    designed = work / "designed_pages.pdf"
    subprocess.run(["node", str(HERE / "tools" / "print_pdf.cjs"), str(html), str(designed)], check=True)
    writer = PdfWriter()
    for source in (designed, args.cad / "Pompeian_Bedroom_Drawing_Set.pdf"):
        for page in PdfReader(source).pages:
            writer.add_page(page)
    writer.add_metadata({"/Title": f"{PROJECT} - Design Review", "/Author": "Prepared with Claude Code",
                         "/Subject": "Neoclassical bedroom 16 x 12 ft: renderings, specifications, CAD sheets"})
    final = args.out / "Pompeian_Bedroom_Design_Review.pdf"
    with open(final, "wb") as fh:
        writer.write(fh)
    args.previews.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(pymupdf.open(final)):
        page.get_pixmap(dpi=60).save(args.previews / f"page_{i + 1:02d}.png")
    print(final, final.stat().st_size // 1024, "KB")


main()
