# server_rack_shelf

A 1U four-post shelf for a standard 19" open server rack (EIA-310).

## Design

Two manufactured designs, three parts to install per shelf:

- **bracket** — bent sheet-metal L. The vertical flange bolts to a rack rail through two EIA-310 holes (M6, cage-nut). The horizontal arm extends away from the rail with a single slotted hole that the top bolts down through. X-symmetric, so the **same part is used at all four corners** — front pair as drawn, rear pair rotated 180° about Z. Manufacture ×4.
- **top** — flat sheet-metal panel matching the rack depth. Two plain mounting holes at the front (at the rail pitch) and two fore-aft slotted holes at the rear. Manufacture ×1.

The slots in the bracket arms and the slots in the rear of the top combine to absorb variation in the rear-rail position. Set `rack_depth_mm` in [params.py](params.py) to your rack's nominal front-to-rear rail spacing; the rear rail can then sit anywhere within roughly ±80 mm of that value without re-manufacturing parts.

Material: 2 mm cold-rolled steel for both parts.

## Build

From the repo root:

```sh
uv run python -m projects.server_rack_shelf
```

Outputs: `exports/bracket.step`, `exports/top.step`.

## Visualize

```sh
uv run cq-studio projects/server_rack_shelf/viewer.py
```

Open <http://127.0.0.1:32323/>. The viewer reloads when `model.py`, `params.py`,
or `viewer.py` change.

## Parameters

Defined in [params.py](params.py). Edit `SHELF_1U_4POST` (or define
a new named instance) and re-run the build. The most likely value to
change is `rack_depth_mm` (and `top.depth_mm` to match).

## Reference dimensions

| Quantity | Value |
| --- | --- |
| 1U height | 44.45 mm (1.75 in) |
| Rack face width | 482.6 mm (19 in) |
| Rail hole horizontal pitch (center-to-center) | 465.1 mm (18.312 in) |

Source: EIA-310-D.
