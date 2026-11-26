"""Assemble every part and light source of the room."""

from .bed import bed_parts
from .casegoods import casegood_parts
from .ceiling import ceiling_parts
from .drapery import window_drapery_parts
from .furnishings import rug_parts
from .lighting import lighting
from .millwork import millwork_parts
from .openings import opening_parts
from .parts import Lamp, Part
from .shell import shell_parts


def room_parts() -> list[Part]:
    fixtures, _ = lighting()
    return [*shell_parts(), *millwork_parts(), *opening_parts(), *ceiling_parts(), *bed_parts(),
            *casegood_parts(), *window_drapery_parts(), *rug_parts(), *fixtures]


def room_lamps() -> list[Lamp]:
    _, lamps = lighting()
    return lamps
