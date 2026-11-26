"""Build the Blender scene (metres) from model parts, lamps and camera views."""

from dataclasses import dataclass
from math import atan2, radians
from pathlib import Path

import bpy
import numpy as np

from ..model.parts import Group, Lamp, Part, Shading
from ..paths import HDRI
from .materials import build_materials

INCH = 0.0254


def _mesh(part: Part) -> bpy.types.Mesh:
    m = part.mesh
    me = bpy.data.meshes.new(part.name)
    me.vertices.add(len(m.verts))
    me.vertices.foreach_set("co", (m.verts * INCH).astype(np.float32).ravel())
    me.loops.add(len(m.loops))
    me.loops.foreach_set("vertex_index", m.loops.astype(np.int32))
    me.polygons.add(len(m.sizes))
    me.polygons.foreach_set("loop_start", (np.cumsum(m.sizes) - m.sizes).astype(np.int32))
    me.update(calc_edges=True)
    me.validate(clean_customdata=False)
    return me


def _smooth(obj: bpy.types.Object, angle_deg: float):
    obj.data.shade_smooth()
    obj.data.set_sharp_from_angle(angle=radians(angle_deg))


def _apply_shading(obj: bpy.types.Object, shading: Shading):
    if shading is Shading.CRISP:
        _smooth(obj, 38.0)
    if shading is Shading.EASED:
        bevel = obj.modifiers.new("ease", "BEVEL")
        bevel.width = 0.12 * INCH
        bevel.segments = 2
        bevel.limit_method = "ANGLE"
        bevel.harden_normals = False
        _smooth(obj, 38.0)
    if shading is Shading.SOFT:
        obj.data.shade_smooth()


def build_objects(parts: list[Part]) -> dict[str, bpy.types.Object]:
    materials = build_materials()
    collections = {}
    for group in Group:
        col = bpy.data.collections.new(group.value)
        bpy.context.scene.collection.children.link(col)
        collections[group] = col
    objects = {}
    for part in parts:
        obj = bpy.data.objects.new(part.name, _mesh(part))
        obj.data.materials.append(materials[part.mat])
        collections[part.group].objects.link(obj)
        _apply_shading(obj, part.shading)
        objects[part.name] = obj
    return objects


def build_lamps(lamps: list[Lamp], scale: float) -> None:
    col = bpy.data.collections.new("LIGHTS")
    bpy.context.scene.collection.children.link(col)
    for lamp in lamps:
        data = bpy.data.lights.new(lamp.name, "POINT")
        data.energy = lamp.watts * scale
        data.shadow_soft_size = lamp.radius * INCH
        data.color = lamp.color
        obj = bpy.data.objects.new(lamp.name, data)
        obj.location = np.asarray(lamp.position) * INCH
        col.objects.link(obj)


@dataclass(frozen=True)
class Daylight:
    sun_azimuth: float  # degrees, compass bearing the sun shines FROM (0 = north, 90 = east)
    sun_elevation: float
    sun_watts: float  # W/m^2 strength of the sun lamp
    sky_strength: float
    hdri_rotation: float  # degrees about z
    lamp_scale: float  # multiplier on interior fixture wattage


def build_environment(day: Daylight) -> None:
    world = bpy.data.worlds.new("world")
    bpy.context.scene.world = world
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    nodes.clear()
    coord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Rotation"].default_value = (0.0, 0.0, radians(day.hdri_rotation))
    env = nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(HDRI), check_existing=True)
    clamp = nodes.new("ShaderNodeVectorMath")  # tame the HDRI sun; the sun lamp replaces it
    clamp.operation = "MINIMUM"
    clamp.inputs[1].default_value = (6.0, 6.0, 6.0)
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = day.sky_strength
    out = nodes.new("ShaderNodeOutputWorld")
    links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], env.inputs["Vector"])
    links.new(env.outputs["Color"], clamp.inputs[0])
    links.new(clamp.outputs["Vector"], bg.inputs["Color"])
    links.new(bg.outputs["Background"], out.inputs["Surface"])

    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = day.sun_watts
    sun.angle = radians(0.6)
    sun.color = (1.0, 0.9, 0.78)
    obj = bpy.data.objects.new("sun", sun)
    # Blender's sun shines along its local -z: tilt down from zenith, then turn to face the azimuth.
    obj.rotation_euler = (radians(90.0 - day.sun_elevation), 0.0, radians(180.0 - day.sun_azimuth))
    bpy.context.scene.collection.objects.link(obj)


def add_window_portals(openings_world: list[tuple[np.ndarray, np.ndarray, float, float]]) -> None:
    """Area-light portals over every window so Cycles samples the sky efficiently."""
    for i, (center, inward, width, height) in enumerate(openings_world):
        data = bpy.data.lights.new(f"portal_{i}", "AREA")
        data.cycles.is_portal = True
        data.shape = "RECTANGLE"
        data.size, data.size_y = width * INCH, height * INCH
        obj = bpy.data.objects.new(f"portal_{i}", data)
        obj.location = np.asarray(center) * INCH
        # Area lights emit along local -z: point it into the room.
        yaw = atan2(inward[1], inward[0])
        obj.rotation_euler = (radians(90.0), 0.0, yaw - radians(90.0))
        bpy.context.scene.collection.objects.link(obj)


@dataclass(frozen=True)
class View:
    name: str
    eye: tuple[float, float, float]  # inches
    look_at: tuple[float, float]  # plan point the camera faces (camera stays level)
    lens_mm: float
    shift_x: float
    shift_y: float
    pitch_deg: float  # 0 = level (verticals stay vertical), 90 = straight down
    ortho_scale: float  # inches across the frame for orthographic views, 0 for perspective


def add_camera(view: View) -> bpy.types.Object:
    cam = bpy.data.cameras.new(view.name)
    cam.type = "ORTHO" if view.ortho_scale > 0 else "PERSP"
    cam.ortho_scale = max(view.ortho_scale, 1.0) * INCH
    cam.lens = view.lens_mm
    cam.sensor_width = 36.0
    cam.shift_x, cam.shift_y = view.shift_x, view.shift_y
    cam.clip_start, cam.clip_end = 0.05, 100.0
    obj = bpy.data.objects.new(view.name, cam)
    obj.location = np.asarray(view.eye) * INCH
    dx, dy = view.look_at[0] - view.eye[0], view.look_at[1] - view.eye[1]
    obj.rotation_euler = (radians(90.0 - view.pitch_deg), 0.0, atan2(dy, dx) - radians(90.0))
    bpy.context.scene.collection.objects.link(obj)
    return obj


def configure_render(samples: int, width: int, height: int, exposure: float) -> None:
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.015
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 10
    scene.cycles.diffuse_bounces = 5
    scene.cycles.glossy_bounces = 5
    scene.cycles.transmission_bounces = 10
    scene.cycles.transparent_max_bounces = 16
    scene.cycles.sample_clamp_indirect = 8.0
    scene.cycles.blur_glossy = 1.0
    scene.cycles.caustics_reflective = False
    scene.cycles.caustics_refractive = False
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = exposure
    scene.render.image_settings.file_format = "PNG"
    scene.render.threads_mode = "AUTO"


def render_view(camera: bpy.types.Object, path: Path) -> None:
    bpy.context.scene.camera = camera
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
