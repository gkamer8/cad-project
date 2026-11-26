"""Render presentation views with Blender (run with the bpy 4.5 interpreter).

    python render_views.py --shots HERO BED --samples 128 --width 1920 --out output/renders
"""

import argparse
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bedroom.model.room import room_lamps, room_parts  # noqa: E402
from bedroom.paths import RUG_IMAGE  # noqa: E402
from bedroom.render import scene  # noqa: E402
from bedroom.render.views import Shots  # noqa: E402
from bedroom.spec import OPENINGS, OpeningKind  # noqa: E402
from bedroom.textures.rug import draw_rug  # noqa: E402

np.seterr(all="raise")


def window_portals() -> list:
    portals = []
    for o in OPENINGS:
        side = o.wall.value
        center = side.to_world(o.center_u, -side.thickness + 0.4, (o.bottom + o.top) / 2)
        portals.extend([(center, side.inward, o.width, o.top - o.bottom)] if o.kind is OpeningKind.WINDOW else [])
    return portals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shots", nargs="+", required=True, choices=[s.name for s in Shots])
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--save-blend", type=Path, required=False)
    args = parser.parse_args()

    draw_rug(RUG_IMAGE)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene.build_objects(room_parts())
    scene.add_window_portals(window_portals())
    args.out.mkdir(parents=True, exist_ok=True)
    for name in args.shots:
        shot = Shots[name].value
        for obj in [o for o in bpy.data.objects if o.type in {"LIGHT", "CAMERA"} and not o.name.startswith("portal")]:
            bpy.data.objects.remove(obj)
        day = shot.mood.value
        for obj in bpy.data.objects:
            obj.hide_render = obj.name.startswith(shot.hide)
        scene.build_lamps(room_lamps(), day.lamp_scale)
        scene.build_environment(day)
        scene.configure_render(args.samples, args.width, args.width * shot.height // shot.width, shot.exposure)
        camera = scene.add_camera(shot.view)
        scene.render_view(camera, args.out / f"{shot.view.name}.png")
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(args.save_blend.resolve()))


main()
