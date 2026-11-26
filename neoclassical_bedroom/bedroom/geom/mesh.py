"""Polygon mesh container shared by the renderer and the CAD exporters.

All geometry in this project is authored in inches (the drawing unit of the CAD
set); the Blender adapter converts to metres only when it builds the scene.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Mesh:
    """Vertices plus polygons stored Blender-style: flat loop indices + face sizes."""

    verts: np.ndarray  # (n, 3) float
    loops: np.ndarray  # (L,) int, vertex index of every face corner, faces concatenated
    sizes: np.ndarray  # (f,) int, corner count of every face

    def moved(self, offset) -> "Mesh":
        return Mesh(self.verts + np.asarray(offset, dtype=float), self.loops, self.sizes)

    def transformed(self, matrix: np.ndarray) -> "Mesh":
        """Apply a 4x4 affine matrix; mirroring matrices also flip the face winding."""
        homo = np.c_[self.verts, np.ones(len(self.verts))] @ matrix.T
        moved = Mesh(homo[:, :3], self.loops, self.sizes)
        return moved.flipped() if np.linalg.det(matrix[:3, :3]) < 0 else moved

    def flipped(self) -> "Mesh":
        starts = np.cumsum(self.sizes) - self.sizes
        order = np.concatenate([np.arange(s + n - 1, s - 1, -1) for s, n in zip(starts, self.sizes)])
        return Mesh(self.verts, self.loops[order], self.sizes)

    def faces(self) -> list[np.ndarray]:
        return np.split(self.loops, np.cumsum(self.sizes)[:-1])


def merge(meshes: list[Mesh]) -> Mesh:
    offsets = np.cumsum([0] + [len(m.verts) for m in meshes[:-1]])
    return Mesh(
        np.concatenate([m.verts for m in meshes]),
        np.concatenate([m.loops + off for m, off in zip(meshes, offsets)]),
        np.concatenate([m.sizes for m in meshes]),
    )


def from_faces(verts, faces) -> Mesh:
    faces = [np.asarray(f, dtype=np.int64) for f in faces]
    return Mesh(np.asarray(verts, dtype=float), np.concatenate(faces), np.array([len(f) for f in faces]))
