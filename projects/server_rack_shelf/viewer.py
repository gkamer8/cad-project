"""cq-studio entry point. Run with `uv run cq-studio projects/server_rack_shelf/viewer.py`."""
from projects.server_rack_shelf.model import build_shelf
from projects.server_rack_shelf.params import SHELF_1U_CANTILEVER


def main():
    return {"shelf": build_shelf(SHELF_1U_CANTILEVER)}
