"""Lean glTF of the room for the browser: one mesh per part, materials named by finish code."""

from pathlib import Path

import bpy

from ..model.parts import Mat, Part
from ..render.materials import srgb_to_linear
from ..render.scene import apply_shading, mesh_from_part


def _plain_material(mat: Mat) -> bpy.types.Material:
    """Base colour only: the explorer builds its own PBR materials keyed on the finish code."""
    m = bpy.data.materials.new(mat.value.code)
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = srgb_to_linear(mat.value.hex_color)
    return m


def export_glb(parts: list[Part], path: Path) -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials = {mat: _plain_material(mat) for mat in Mat}
    for part in parts:
        obj = bpy.data.objects.new(part.name, mesh_from_part(part))
        obj.data.materials.append(materials[part.mat])
        bpy.context.scene.collection.objects.link(obj)
        apply_shading(obj, part.shading)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_apply=False, export_texcoords=False,
                              export_normals=True, export_materials="EXPORT", export_cameras=False,
                              export_lights=False, export_yup=True, export_extras=False)
