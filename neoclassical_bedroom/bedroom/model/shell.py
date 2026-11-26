"""Room shell: floor slab, ceiling slab and thick walls with true window/door openings."""

from ..geom.mesh import Mesh, from_faces, merge
from ..geom.prims import box
from ..spec import CEILING_H, CHAIR_RAIL_TOP, ROOM_L, ROOM_W, Opening, OpeningKind, Wall, openings_on
from .parts import Group, Mat, Part, Shading

OVERLAP = 8.0  # walls run past the corners so the shell is light-tight
FLOOR_Z = -1.0
TOP_Z = CEILING_H + 1.0


def on_wall(mesh: Mesh, wall: Wall) -> Mesh:
    """Map wall-local geometry (x = along wall, y = into room, z = up) into the world."""
    return mesh.transformed(wall.value.frame())


def _quad(u0: float, u1: float, z0: float, z1: float, y: float, facing_room: bool) -> list:
    corners = [(u0, y, z0), (u1, y, z0), (u1, y, z1), (u0, y, z1)]  # natural winding faces -y
    return corners[::-1] if facing_room else corners


def _cells(wall: Wall) -> list[tuple[float, float, float, float]]:
    ops = openings_on(wall)
    us = sorted({-OVERLAP, wall.value.length + OVERLAP, *[u for o in ops for u in (o.u0, o.u1)]})
    zs = sorted({FLOOR_Z, CHAIR_RAIL_TOP, TOP_Z, *[z for o in ops for z in (o.bottom, o.top)]})
    inside = [(o.u0, o.u1, o.bottom, o.top) for o in ops]
    return [
        (u0, u1, z0, z1)
        for u0, u1 in zip(us[:-1], us[1:])
        for z0, z1 in zip(zs[:-1], zs[1:])
        if not any(a <= u0 and u1 <= b and c <= z0 and z1 <= d for a, b, c, d in inside)
    ]


def _faces_mesh(quads: list) -> Mesh:
    verts = [v for q in quads for v in q]
    return from_faces(verts, [range(4 * i, 4 * i + 4) for i in range(len(quads))])


def _jambs(opening: Opening, thickness: float) -> list:
    """Reveal faces lining an opening (no sill face for doors)."""
    u0, u1, z0, z1, t = opening.u0, opening.u1, opening.bottom, opening.top, -thickness
    quads = [
        [(u0, 0, z0), (u0, t, z0), (u0, t, z1), (u0, 0, z1)],
        [(u1, 0, z1), (u1, t, z1), (u1, t, z0), (u1, 0, z0)],
        [(u0, 0, z1), (u0, t, z1), (u1, t, z1), (u1, 0, z1)],
    ]
    sill = [(u1, 0, z0), (u1, t, z0), (u0, t, z0), (u0, 0, z0)]
    faces = quads + ([sill] if opening.kind is OpeningKind.WINDOW else [])
    return [q[::-1] for q in faces]  # wound to face into the opening


def wall_parts(wall: Wall) -> list[Part]:
    side = wall.value
    t = side.thickness
    cells = _cells(wall)
    upper = [_quad(*c[:2], *c[2:], 0.0, True) for c in cells if c[2] >= CHAIR_RAIL_TOP]
    lower = [_quad(*c[:2], *c[2:], 0.0, True) for c in cells if c[3] <= CHAIR_RAIL_TOP]
    outer = [_quad(*c[:2], *c[2:], -t, False) for c in cells]
    ends = [
        [(-OVERLAP, -t, FLOOR_Z), (-OVERLAP, -t, TOP_Z), (-OVERLAP, 0, TOP_Z), (-OVERLAP, 0, FLOOR_Z)],
        [(side.length + OVERLAP, 0, TOP_Z), (side.length + OVERLAP, -t, TOP_Z),
         (side.length + OVERLAP, -t, FLOOR_Z), (side.length + OVERLAP, 0, FLOOR_Z)],
    ]
    jambs = [q for o in openings_on(wall) for q in _jambs(o, t)]
    name = side.label.lower()
    return [
        Part(f"wall_{name}_upper", on_wall(_faces_mesh(upper), wall), Mat.WALL_RED, Group.SHELL, Shading.FLAT),
        Part(f"wall_{name}_dado", on_wall(_faces_mesh(lower), wall), Mat.TRIM_IVORY, Group.SHELL, Shading.FLAT),
        Part(f"wall_{name}_outer", on_wall(_faces_mesh(outer + ends), wall), Mat.WALL_SHELL, Group.SHELL,
             Shading.FLAT),
    ] + ([Part(f"wall_{name}_reveals", on_wall(_faces_mesh(jambs), wall), Mat.TRIM_IVORY, Group.SHELL,
               Shading.FLAT)] if jambs else [])


def shell_parts() -> list[Part]:
    floor = box((-OVERLAP, -OVERLAP, FLOOR_Z), (ROOM_L + OVERLAP, ROOM_W + OVERLAP, 0.0))
    ceiling = box((-OVERLAP, -OVERLAP, CEILING_H), (ROOM_L + OVERLAP, ROOM_W + OVERLAP, TOP_Z))
    parts = [
        Part("floor_parquet", floor, Mat.PARQUET, Group.SHELL, Shading.FLAT),
        Part("ceiling", ceiling, Mat.CEILING, Group.SHELL, Shading.FLAT),
    ]
    for wall in Wall:
        parts.extend(wall_parts(wall))
    return parts


def merged(parts: list[Part], name: str) -> Part:
    """Combine same-material parts into one object (keeps scene object counts sane)."""
    first = parts[0]
    return Part(name, merge([p.mesh for p in parts]), first.mat, first.group, first.shading)
