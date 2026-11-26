"""Generate the AutoCAD deliverables (run with the project's Python 3.11 environment).

    python build_cad.py --out output/cad

Writes the 2D drawing set (DXF, paper-space sheets with title blocks), the 3D mesh
model (DXF), a vector PDF of the sheets and PNG previews of each sheet.
"""

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bedroom.drawings.export import sheets_to_pdf, write_model_dxf  # noqa: E402
from bedroom.drawings.sheets import build_drawing_set  # noqa: E402
from bedroom.model.room import room_parts  # noqa: E402

np.seterr(all="raise")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--previews", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    parts = room_parts()
    doc = build_drawing_set(parts)
    doc.saveas(args.out / "Pompeian_Bedroom_Drawings.dxf")
    write_model_dxf(parts, args.out / "Pompeian_Bedroom_3D_Model.dxf")
    for preview in sheets_to_pdf(doc, args.out / "Pompeian_Bedroom_Drawing_Set.pdf", args.previews):
        print(preview)


main()
