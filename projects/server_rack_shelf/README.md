# server_rack_shelf

A 1U cantilever shelf for a standard 19" open server rack (EIA-310).

## Design

Two manufactured parts:

- **bracket** — bent sheet-metal L. The vertical flange bolts to a rack rail through two EIA-310 holes (M6, cage-nut). The horizontal arm cantilevers back into the rack and carries two slotted holes that the top bolts down through. Mirror-symmetric, so one part fits both sides.
- **top** — flat sheet-metal panel sized to the rack-face width, with four plain holes at the rack-rail pitch.

Depth is adjustable in place: the slots in the bracket arms give 40 mm of fore/aft slide for the top before you tighten the bolts. No part swap, no precise measurement required.

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

Defined in [params.py](params.py). Edit `SHELF_1U_CANTILEVER` (or define
a new named instance) and re-run the build.

## Reference dimensions

| Quantity | Value |
| --- | --- |
| 1U height | 44.45 mm (1.75 in) |
| Rack face width | 482.6 mm (19 in) |
| Rail hole horizontal pitch (center-to-center) | 465.1 mm (18.312 in) |

Source: EIA-310-D.
