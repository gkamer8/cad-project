"""Download the CC0 textures / HDRI (Poly Haven) and OFL fonts (Google Fonts) into assets/.

    python tools/fetch_assets.py
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bedroom.paths import FONTS, FONTS_CSS, TEXTURES  # noqa: E402

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; asset-fetch/1.0)"}
TEXTURE_SETS = {  # Poly Haven asset -> resolution
    "herringbone_parquet": "4k", "velour_velvet": "2k", "crepe_satin": "2k", "floral_jacquard": "2k",
    "rough_linen": "2k", "quatrefoil_jacquard_fabric": "2k", "marble_01": "2k",
}
MAPS = {"Diffuse": "diff", "nor_gl": "nor_gl", "Rough": "rough", "Displacement": "disp"}
FONT_FAMILIES = ("Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500", "Inter:wght@300;400;500;600")


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120) as r:
        return r.read()


def save(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(get(url))
    print(dest.relative_to(dest.parents[2]), dest.stat().st_size // 1024, "KB")


def main() -> None:
    for asset, res in TEXTURE_SETS.items():
        files = json.loads(get(f"https://api.polyhaven.com/files/{asset}"))
        for key, short in MAPS.items():
            save(files[key][res]["jpg"]["url"], TEXTURES / asset / f"{short}.jpg")
    hdri = json.loads(get("https://api.polyhaven.com/files/borghese_gardens"))
    save(hdri["hdri"]["4k"]["hdr"]["url"], TEXTURES / "hdri" / "borghese_gardens_4k.hdr")
    css_out = []
    for family in FONT_FAMILIES:  # plain user agent -> Google serves TrueType files
        css = urllib.request.urlopen(f"https://fonts.googleapis.com/css2?family={family}", timeout=60).read().decode()
        for i, url in enumerate(re.findall(r"url\((https://[^)]+\.ttf)\)", css)):
            dest = FONTS / f"{family.split(':')[0].replace('+', '')}_{i}.ttf"
            save(url, dest)
            css = css.replace(url, dest.as_uri())
        css_out.append(css)
    FONTS_CSS.write_text("\n".join(css_out))


main()
