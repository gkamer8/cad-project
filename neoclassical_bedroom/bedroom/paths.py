"""Filesystem locations used by the build (assets are fetched by tools/fetch_assets.py)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TEXTURES = ASSETS / "polyhaven"
HDRI = TEXTURES / "hdri" / "borghese_gardens_4k.hdr"
FONTS = ASSETS / "fonts"
FONTS_CSS = FONTS / "fonts.css"
OUTPUT = ROOT / "output"
RUG_IMAGE = OUTPUT / "textures" / "rug.png"
