"""Camera views and lighting moods for the presentation renders."""

from dataclasses import dataclass
from enum import Enum

from .scene import Daylight, View


class Mood(Enum):
    AFTERNOON = Daylight(sun_azimuth=232.0, sun_elevation=24.0, sun_watts=7.0, sky_strength=2.2,
                         hdri_rotation=200.0, lamp_scale=1.0)
    EVENING = Daylight(sun_azimuth=250.0, sun_elevation=-6.0, sun_watts=0.0, sky_strength=0.035,
                       hdri_rotation=200.0, lamp_scale=3.2)


@dataclass(frozen=True)
class Shot:
    view: View
    mood: Mood
    exposure: float
    width: int
    height: int
    hide: tuple[str, ...]  # part-name prefixes left out of this shot


CEILING_PARTS = ("ceiling", "cornice", "chandelier", "canopy")


class Shots(Enum):
    HERO = Shot(View("hero", (184.0, 72.0, 50.0), (0.0, 72.0), 18.0, 0.0, 0.1, 0.0, 0.0),
                Mood.AFTERNOON, 1.9, 3, 2, ())
    BED = Shot(View("bed", (132.0, 20.0, 44.0), (14.0, 84.0), 22.0, 0.0, 0.06, 0.0, 0.0),
               Mood.AFTERNOON, 1.8, 3, 2, ())
    DOOR_WALL = Shot(View("door_wall", (40.0, 120.0, 52.0), (192.0, 44.0), 18.0, 0.0, 0.08, 0.0, 0.0),
                     Mood.AFTERNOON, 1.9, 3, 2, ())
    EVENING = Shot(View("evening", (184.0, 72.0, 50.0), (0.0, 72.0), 18.0, 0.0, 0.1, 0.0, 0.0),
                   Mood.EVENING, 1.0, 3, 2, ())
    CANOPY = Shot(View("canopy", (70.0, 112.0, 40.0), (0.0, 50.0), 26.0, 0.0, 0.16, 0.0, 0.0),
                  Mood.AFTERNOON, 1.8, 3, 2, ())
    PLAN = Shot(View("plan", (96.0, 72.0, 300.0), (96.0, 400.0), 50.0, 0.0, 0.0, 90.0, 214.0),
                Mood.AFTERNOON, 1.0, 4, 3, CEILING_PARTS)
