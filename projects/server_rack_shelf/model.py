"""CadQuery models for the server-rack shelf parts.

The shelf is two manufactured parts:

* ``bracket`` — a bent sheet-metal L. The vertical flange bolts to a
  rack rail through two EIA-310 holes; the horizontal arm cantilevers
  back into the rack and carries two depth-adjust slots that the top
  bolts down through. The part is mirror-symmetric about its width
  axis, so one design serves both rails.
* ``top`` — a flat sheet-metal panel with four plain mounting holes at
  the rack rail pitch, bolted down through the bracket slots.

The bracket's local coordinate system:
* origin at the centerline of the front-bottom edge (the bend),
* +X spans the bracket width,
* +Y points backward into the rack,
* +Z points up.

The top's local coordinate system:
* origin centered in X and on the front edge of the panel,
* +Y points backward into the rack,
* +Z points up; the panel is centered on Z=0.
"""
import cadquery as cq

from projects.server_rack_shelf.params import (
    BracketParams,
    EIA_HOLE_Z_OFFSET_MM,
    RAIL_HOLE_PITCH_HORIZONTAL_MM,
    TopParams,
)


def build_bracket(params: BracketParams) -> cq.Workplane:
    t = params.thickness_mm
    w = params.width_mm
    h = params.flange_height_mm
    arm_length = params.arm_length_mm

    flange = (
        cq.Workplane("XY")
        .box(w, t, h, centered=(True, False, False))
        .faces("<Y")
        .workplane(centerOption="CenterOfBoundBox")
        .pushPoints([(0, -EIA_HOLE_Z_OFFSET_MM), (0, EIA_HOLE_Z_OFFSET_MM)])
        .hole(params.mount_hole_diameter_mm)
    )

    arm = (
        cq.Workplane("XY")
        .workplane(offset=-t / 2)
        .box(w, arm_length, t, centered=(True, False, True))
        .faces(">Z")
        .workplane(centerOption="CenterOfBoundBox")
        .pushPoints(
            [
                (0, params.front_slot_center_y_mm - arm_length / 2),
                (0, params.rear_slot_center_y_mm - arm_length / 2),
            ]
        )
        .slot2D(params.slot_length_mm, params.mount_hole_diameter_mm, angle=90)
        .cutThruAll()
    )

    return flange.union(arm)


def build_top(params: TopParams) -> cq.Workplane:
    half_pitch = RAIL_HOLE_PITCH_HORIZONTAL_MM / 2
    half_depth = params.depth_mm / 2

    return (
        cq.Workplane("XY")
        .box(
            params.width_mm,
            params.depth_mm,
            params.thickness_mm,
            centered=(True, False, True),
        )
        .faces(">Z")
        .workplane(centerOption="CenterOfBoundBox")
        .pushPoints(
            [
                (-half_pitch, params.front_hole_y_mm - half_depth),
                (half_pitch, params.front_hole_y_mm - half_depth),
                (-half_pitch, params.rear_hole_y_mm - half_depth),
                (half_pitch, params.rear_hole_y_mm - half_depth),
            ]
        )
        .hole(params.mount_hole_diameter_mm)
    )
