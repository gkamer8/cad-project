"""Export the 3D model for Autodesk tools (run with the bpy 4.5 interpreter).

    python export_3d.py --out output/cad

FBX (3ds Max, Maya, Autodesk Viewer) and OBJ + MTL (universal). FBX carries unit
metadata; OBJ is written in inches to match the DXF drawings.
"""

import argparse
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bedroom.model.room import room_parts  # noqa: E402
from bedroom.render import scene  # noqa: E402

np.seterr(all="raise")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "IMPERIAL"
    bpy.context.scene.unit_settings.length_unit = "INCHES"
    scene.build_objects(room_parts())
    for mat in bpy.data.materials:  # exported viewport colour = finish colour
        principled = [n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"]
        mat.diffuse_color = principled[0].inputs["Base Color"].default_value if principled else mat.diffuse_color
    stem = args.out / "Pompeian_Bedroom_3D"
    bpy.ops.export_scene.fbx(filepath=str(stem.with_suffix(".fbx")), use_selection=False, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", use_mesh_modifiers=True, mesh_smooth_type="FACE",
                             path_mode="STRIP", axis_forward="-Y", axis_up="Z")
    bpy.ops.wm.obj_export(filepath=str(stem.with_suffix(".obj")), apply_modifiers=True, export_materials=True,
                          global_scale=1.0 / 0.0254, forward_axis="NEGATIVE_Y", up_axis="Z", path_mode="STRIP")


main()
