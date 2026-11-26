"""Hidden-line linework from the 3D model: project every mesh component, order by
distance to the viewer, and keep only the outline portions nearer parts do not hide.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from shapely.geometry.base import BaseGeometry

from ..geom.mesh import Mesh

MIN_AREA = 0.3  # sq in; smaller specks (beads, gallery posts) are left out of drawings


@dataclass(frozen=True)
class Silhouette:
    shape: BaseGeometry  # projected outline, drawing coordinates (inches)
    near: float  # larger = closer to the viewer
    low: float  # lowest point along the viewing-independent 'height' axis (for plan cuts)


def _fan_triangles(mesh: Mesh) -> tuple[np.ndarray, np.ndarray]:
    """(t, 3) vertex indices and the face each triangle came from."""
    starts = np.cumsum(mesh.sizes) - mesh.sizes
    per_face = mesh.sizes - 2
    face = np.repeat(np.arange(len(mesh.sizes)), per_face)
    k = np.arange(per_face.sum()) - np.repeat(np.cumsum(per_face) - per_face, per_face) + 1
    first = mesh.loops[starts[face]]
    return np.stack([first, mesh.loops[starts[face] + k], mesh.loops[starts[face] + k + 1]], axis=1), face


def component_triangles(mesh: Mesh) -> list[np.ndarray]:
    """Triangles (t, 3, 3) of every connected component of a mesh."""
    n_v, n_f = len(mesh.verts), len(mesh.sizes)
    face_of_loop = np.repeat(np.arange(n_f), mesh.sizes)
    graph = coo_matrix((np.ones(len(mesh.loops)), (mesh.loops, n_v + face_of_loop)), shape=(n_v + n_f,) * 2)
    _, labels = connected_components(graph, directed=False)
    tris, face = _fan_triangles(mesh)
    tri_label = labels[n_v + face]
    order = np.argsort(tri_label, kind="stable")
    bounds = np.flatnonzero(np.diff(tri_label[order])) + 1
    return [mesh.verts[tris[idx]] for idx in np.split(order, bounds)]


def outline(tri2d: np.ndarray) -> BaseGeometry:
    """Union of projected triangles (t, 3, 2)."""
    a, b, c = tri2d[:, 0], tri2d[:, 1], tri2d[:, 2]
    area = 0.5 * np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1]))
    keep = tri2d[area > 1e-5]
    rings = np.concatenate([keep, keep[:, :1]], axis=1)
    return shapely.union_all(shapely.polygons(rings)).buffer(0.01).buffer(-0.01).simplify(0.04)


def silhouettes(meshes: list[Mesh], project: Callable[[np.ndarray], tuple[np.ndarray, np.ndarray]],
                keep: Callable[[np.ndarray], bool]) -> list[Silhouette]:
    """``project`` maps (t, 3, 3) world triangles to ((t, 3, 2) drawing coords, (t, 3) nearness)."""
    out = []
    for mesh in meshes:
        for tris in component_triangles(mesh):
            flat, near = project(tris)
            shape = outline(flat) if keep(tris) else shapely.Polygon()
            out.extend([Silhouette(shape, float(near.max()), float(tris[..., 2].min()))]
                       if shape.area > MIN_AREA else [])
    return out


def hidden_line(sils: list[Silhouette]) -> tuple[list[BaseGeometry], BaseGeometry]:
    """Visible outline segments (nearest first) and the union of everything drawn."""
    covered = shapely.Polygon()
    visible = []
    for s in sorted(sils, key=lambda s: -s.near):
        visible.append(s.shape.boundary.difference(covered))
        covered = covered.union(s.shape)
    return visible, covered


def line_parts(geom: BaseGeometry) -> list[np.ndarray]:
    """Coordinate arrays of every line piece in a (multi)line geometry, merged end to end."""
    pieces = [p for p in shapely.get_parts(geom) if p.geom_type in ("LineString", "LinearRing")]
    merged = shapely.line_merge(shapely.multilinestrings(pieces))
    return [np.asarray(p.coords) for p in shapely.get_parts(merged)]
