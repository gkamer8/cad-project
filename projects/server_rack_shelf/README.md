# server_rack_shelf

A shelf for a standard 19" open server rack (EIA-310).

## Status

Scaffold only. `build_shelf` currently returns a flat plate at rack-face
width — the real cantilever geometry, mounting flange, and hole pattern
land in the next feature branch.

## Build

From the repo root:

```sh
uv run python -m projects.server_rack_shelf
```

Output: `exports/shelf.step`.

## Visualize

```sh
uv run cq-studio projects/server_rack_shelf/viewer.py
```

Open <http://127.0.0.1:32323/>. The viewer reloads when `model.py`, `params.py`,
or `viewer.py` change.

## Parameters

Defined in [params.py](params.py). Edit `SHELF_1U_CANTILEVER` (or define
a new named instance) and re-run the build.

## Reference dimensions

| Quantity | Value |
| --- | --- |
| 1U height | 44.45 mm (1.75 in) |
| Rack face width | 482.6 mm (19 in) |
| Rail hole horizontal pitch (center-to-center) | 465.1 mm (18.312 in) |

Source: EIA-310-D.
