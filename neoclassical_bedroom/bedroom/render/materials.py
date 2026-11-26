"""Cycles shader networks for every finish in ``Mat`` (Blender 4.5 node API)."""

from collections.abc import Callable
from pathlib import Path

import bpy

from ..model.parts import Mat
from ..paths import RUG_IMAGE, TEXTURES
from ..spec import RUG

INCH = 0.0254


def srgb_to_linear(hex_color: str) -> tuple[float, float, float, float]:
    rgb = [int(hex_color.lstrip("#")[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return (*lin, 1.0)


class Graph:
    """Tiny helper around a material node tree."""

    def __init__(self, name: str):
        self.mat = bpy.data.materials.new(name)
        self.mat.use_nodes = True
        self.nodes = self.mat.node_tree.nodes
        self.links = self.mat.node_tree.links
        self.nodes.clear()
        self.out = self.nodes.new("ShaderNodeOutputMaterial")

    def node(self, kind: str, **inputs):
        n = self.nodes.new(kind)
        for key, value in inputs.items():
            n.inputs[key].default_value = value
        return n

    def link(self, src, dst):
        self.links.new(src, dst)

    def finish(self, shader_socket) -> bpy.types.Material:
        self.link(shader_socket, self.out.inputs["Surface"])
        return self.mat

    def coords(self, scale_m: float):
        tc = self.nodes.new("ShaderNodeTexCoord")
        mp = self.node("ShaderNodeMapping", Scale=(1 / scale_m, 1 / scale_m, 1 / scale_m))
        self.link(tc.outputs["Object"], mp.inputs["Vector"])
        return mp.outputs["Vector"]

    def image(self, path: Path, vector, color: bool, box: bool):
        tex = self.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(path), check_existing=True)
        tex.image.colorspace_settings.name = "sRGB" if color else "Non-Color"
        tex.projection = "BOX" if box else "FLAT"
        tex.projection_blend = 0.25
        self.link(vector, tex.inputs["Vector"])
        return tex

    def normal_map(self, path: Path, vector, strength: float, box: bool):
        tex = self.image(path, vector, color=False, box=box)
        nm = self.node("ShaderNodeNormalMap", Strength=strength)
        self.link(tex.outputs["Color"], nm.inputs["Color"])
        return nm.outputs["Normal"]

    def noise(self, vector, scale: float, detail: float):
        n = self.node("ShaderNodeTexNoise", Scale=scale, Detail=detail)
        self.link(vector, n.inputs["Vector"])
        return n

    def ramp(self, fac, stops: list[tuple[float, tuple]]):
        r = self.nodes.new("ShaderNodeValToRGB")
        elements = r.color_ramp.elements
        elements[0].position, elements[0].color = stops[0]
        elements[1].position, elements[1].color = stops[-1]
        for position, color in stops[1:-1]:
            elements.new(position).color = color
        self.link(fac, r.inputs["Fac"])
        return r.outputs["Color"]

    def mix_color(self, fac, a, b):
        m = self.nodes.new("ShaderNodeMix")
        m.data_type = "RGBA"
        sockets = {s.identifier: s for s in m.inputs}
        for socket, value in ((sockets["Factor_Float"], fac), (sockets["A_Color"], a), (sockets["B_Color"], b)):
            if isinstance(value, bpy.types.NodeSocket):
                self.link(value, socket)
            else:
                socket.default_value = value
        return {s.identifier: s for s in m.outputs}["Result_Color"]

    def bump(self, height, strength: float, distance: float):
        b = self.node("ShaderNodeBump", Strength=strength, Distance=distance)
        self.link(height, b.inputs["Height"])
        return b.outputs["Normal"]

    def principled(self, color, **inputs):
        p = self.node("ShaderNodeBsdfPrincipled", **inputs)
        if isinstance(color, bpy.types.NodeSocket):
            self.link(color, p.inputs["Base Color"])
        else:
            p.inputs["Base Color"].default_value = color
        return p


def _paint(mat: Mat, roughness: float, bump: float) -> bpy.types.Material:
    g = Graph(mat.name)
    v = g.coords(1.0)
    tint = g.noise(v, 1.6, 2.0)
    base = srgb_to_linear(mat.value.hex_color)
    darker = tuple(c * 0.93 for c in base[:3]) + (1.0,)
    color = g.mix_color(tint.outputs["Fac"], darker, base)
    p = g.principled(color, Roughness=roughness)
    g.link(g.bump(g.noise(v, 900.0, 3.0).outputs["Fac"], bump, 0.0006), p.inputs["Normal"])
    return g.finish(p.outputs["BSDF"])


def _gilt(mat: Mat) -> bpy.types.Material:
    g = Graph(mat.name)
    v = g.coords(1.0)
    ao = g.node("ShaderNodeAmbientOcclusion", Distance=0.012)
    gold = srgb_to_linear("#D9B163")
    bole = srgb_to_linear("#6B3A1F")
    color = g.mix_color(ao.outputs["AO"], bole, gold)
    rough = g.ramp(g.noise(v, 60.0, 4.0).outputs["Fac"], [(0.3, (0.18,) * 3 + (1,)), (0.7, (0.42,) * 3 + (1,))])
    p = g.principled(color, Metallic=1.0)
    g.link(rough, p.inputs["Roughness"])
    return g.finish(p.outputs["BSDF"])


def _parquet(mat: Mat) -> bpy.types.Material:
    g = Graph(mat.name)
    v = g.coords(3.4)
    diff = g.image(TEXTURES / "herringbone_parquet" / "diff.jpg", v, color=True, box=False)
    rough = g.image(TEXTURES / "herringbone_parquet" / "rough.jpg", v, color=False, box=False)
    warm = g.mix_color(0.35, diff.outputs["Color"], srgb_to_linear("#7A4A26"))
    p = g.principled(warm, **{"Coat Weight": 0.35, "Coat Roughness": 0.12})
    g.link(rough.outputs["Color"], p.inputs["Roughness"])
    g.link(g.normal_map(TEXTURES / "herringbone_parquet" / "nor_gl.jpg", v, 0.6, box=False), p.inputs["Normal"])
    return g.finish(p.outputs["BSDF"])


def _fabric(mat: Mat, texture: str, tile_m: float, roughness: float, sheen: float, normal: float):
    g = Graph(mat.name)
    v = g.coords(tile_m)
    weave = g.image(TEXTURES / texture / "diff.jpg", v, color=False, box=True)
    shade = g.ramp(weave.outputs["Color"], [(0.0, (0.82,) * 3 + (1,)), (1.0, (1.0,) * 3 + (1,))])
    color = g.mix_color(1.0, srgb_to_linear(mat.value.hex_color), shade)
    mix = color.node
    mix.blend_type = "MULTIPLY"
    p = g.principled(color, Roughness=roughness, **{"Sheen Weight": sheen, "Sheen Roughness": 0.35,
                                                     "Sheen Tint": (1.0, 0.85, 0.8, 1.0)})
    g.link(g.normal_map(TEXTURES / texture / "nor_gl.jpg", v, normal, box=True), p.inputs["Normal"])
    return g.finish(p.outputs["BSDF"])


def _damask(mat: Mat) -> bpy.types.Material:
    g = Graph(mat.name)
    v = g.coords(0.55)
    pattern = g.image(TEXTURES / "floral_jacquard" / "diff.jpg", v, color=False, box=True)
    motif = g.ramp(pattern.outputs["Color"], [(0.18, (0.0,) * 3 + (1,)), (0.32, (1.0,) * 3 + (1,))])
    color = g.mix_color(motif, srgb_to_linear("#5E0F14"), srgb_to_linear("#9C2A2E"))
    rough = g.mix_color(motif, (0.7, 0.7, 0.7, 1.0), (0.3, 0.3, 0.3, 1.0))
    p = g.principled(color, **{"Sheen Weight": 0.4, "Sheen Tint": (1.0, 0.8, 0.75, 1.0)})
    g.link(rough, p.inputs["Roughness"])
    g.link(g.normal_map(TEXTURES / "floral_jacquard" / "nor_gl.jpg", v, 0.4, box=True), p.inputs["Normal"])
    return g.finish(p.outputs["BSDF"])


def _lacquer(mat: Mat) -> bpy.types.Material:
    g = Graph(mat.name)
    p = g.principled(srgb_to_linear(mat.value.hex_color), Roughness=0.35,
                     **{"Coat Weight": 1.0, "Coat Roughness": 0.06})
    return g.finish(p.outputs["BSDF"])


def _marble(mat: Mat) -> bpy.types.Material:
    g = Graph(mat.name)
    v = g.coords(1.0)
    n = g.node("ShaderNodeTexNoise", Scale=3.0, Detail=10.0, Roughness=0.6, Distortion=2.2)
    g.link(v, n.inputs["Vector"])
    veins = g.ramp(n.outputs["Fac"], [(0.44, (0.86, 0.85, 0.83, 1)), (0.495, (0.42, 0.42, 0.44, 1)),
                                       (0.505, (0.55, 0.55, 0.57, 1)), (0.56, (0.86, 0.85, 0.83, 1))])
    p = g.principled(veins, Roughness=0.08, **{"Subsurface Weight": 0.15,
                                               "Subsurface Radius": (0.01, 0.01, 0.01)})
    return g.finish(p.outputs["BSDF"])


def _thin_glass(mat: Mat, tint: tuple) -> bpy.types.Material:
    g = Graph(mat.name)
    lw = g.node("ShaderNodeLayerWeight", Blend=0.08)
    clear = g.node("ShaderNodeBsdfTransparent", Color=tint)
    gloss = g.node("ShaderNodeBsdfGlossy", Roughness=0.01)
    mix = g.node("ShaderNodeMixShader")
    g.link(lw.outputs["Fresnel"], mix.inputs[0])
    g.link(clear.outputs[0], mix.inputs[1])
    g.link(gloss.outputs[0], mix.inputs[2])
    return g.finish(mix.outputs[0])


def _crystal(mat: Mat) -> bpy.types.Material:
    g = Graph(mat.name)
    path = g.nodes.new("ShaderNodeLightPath")
    glass = g.node("ShaderNodeBsdfGlass", IOR=1.6, Roughness=0.0)
    clear = g.node("ShaderNodeBsdfTransparent")
    mix = g.node("ShaderNodeMixShader")
    g.link(path.outputs["Is Shadow Ray"], mix.inputs[0])
    g.link(glass.outputs[0], mix.inputs[1])
    g.link(clear.outputs[0], mix.inputs[2])
    return g.finish(mix.outputs[0])


def _simple(mat: Mat, **inputs) -> bpy.types.Material:
    g = Graph(mat.name)
    return g.finish(g.principled(srgb_to_linear(mat.value.hex_color), **inputs).outputs["BSDF"])


def _shade(mat: Mat) -> bpy.types.Material:
    g = Graph(mat.name)
    color = srgb_to_linear(mat.value.hex_color)
    front = g.principled(color, Roughness=0.7, **{"Sheen Weight": 0.3})
    glow = g.node("ShaderNodeBsdfTranslucent", Color=(1.0, 0.78, 0.5, 1.0))
    mix = g.node("ShaderNodeMixShader", Fac=0.55)
    g.link(front.outputs[0], mix.inputs[1])
    g.link(glow.outputs[0], mix.inputs[2])
    return g.finish(mix.outputs[0])


def _bulb(mat: Mat) -> bpy.types.Material:
    g = Graph(mat.name)
    e = g.node("ShaderNodeEmission", Color=srgb_to_linear(mat.value.hex_color), Strength=18.0)
    return g.finish(e.outputs[0])


def _rug(mat: Mat) -> bpy.types.Material:
    """Generated rug artwork mapped over the rug footprint (u along x, v along y)."""
    g = Graph(mat.name)
    place, (width, depth, _) = RUG.placements[0], RUG.size
    length_x, length_y = depth * INCH, width * INCH
    x0, y0 = place.x * INCH - length_x / 2, place.y * INCH - length_y / 2
    tc = g.nodes.new("ShaderNodeTexCoord")
    mp = g.node("ShaderNodeMapping", Scale=(1 / length_x, 1 / length_y, 1.0),
                Location=(-x0 / length_x, -y0 / length_y, 0.0))
    g.link(tc.outputs["Object"], mp.inputs["Vector"])
    tex = g.image(RUG_IMAGE, mp.outputs["Vector"], color=True, box=False)
    pile = g.noise(g.coords(1.0), 700.0, 2.0)
    p = g.principled(tex.outputs["Color"], Roughness=0.95, **{"Sheen Weight": 0.7, "Sheen Roughness": 0.5})
    g.link(g.bump(pile.outputs["Fac"], 0.35, 0.001), p.inputs["Normal"])
    return g.finish(p.outputs["BSDF"])


BUILDERS: dict[Mat, Callable[[Mat], bpy.types.Material]] = {
    Mat.WALL_RED: lambda m: _paint(m, 0.55, 0.06),
    Mat.TRIM_IVORY: lambda m: _paint(m, 0.3, 0.04),
    Mat.CEILING: lambda m: _paint(m, 0.85, 0.05),
    Mat.GILT: _gilt,
    Mat.PARQUET: _parquet,
    Mat.LACQUER: _lacquer,
    Mat.MARBLE: _marble,
    Mat.DAMASK: _damask,
    Mat.SILK_RED: lambda m: _fabric(m, "crepe_satin", 0.25, 0.38, 0.7, 0.3),
    Mat.VELVET: lambda m: _fabric(m, "velour_velvet", 0.3, 0.85, 1.0, 0.5),
    Mat.SILK_IVORY: lambda m: _fabric(m, "crepe_satin", 0.25, 0.4, 0.6, 0.3),
    Mat.LINEN: lambda m: _fabric(m, "rough_linen", 0.2, 0.62, 0.4, 0.25),
    Mat.RUG: _rug,
    Mat.BRASS: lambda m: _simple(m, Metallic=1.0, Roughness=0.22),
    Mat.PORCELAIN: lambda m: _simple(m, Roughness=0.1, **{"Coat Weight": 1.0, "Coat Roughness": 0.03}),
    Mat.SHADE: _shade,
    Mat.TOLE: lambda m: _simple(m, Roughness=0.32, **{"Coat Weight": 0.5}),
    Mat.GLASS: lambda m: _thin_glass(m, (0.96, 0.98, 0.98, 1.0)),
    Mat.MIRROR: lambda m: _simple(m, Metallic=1.0, Roughness=0.015),
    Mat.CRYSTAL: _crystal,
    Mat.WAX: lambda m: _simple(m, Roughness=0.45, **{"Subsurface Weight": 0.4,
                                                     "Subsurface Radius": (0.02, 0.012, 0.008)}),
    Mat.BULB: _bulb,
    Mat.WALL_SHELL: lambda m: _simple(m, Roughness=0.9),
}


def build_materials() -> dict[Mat, bpy.types.Material]:
    return {mat: BUILDERS[mat](mat) for mat in Mat}
