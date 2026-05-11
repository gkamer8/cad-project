# cad-project

CAD designs authored in [CadQuery](https://github.com/CadQuery/cadquery), kept in source so revisions are diffable and outputs are reproducible.

## Layout

```
projects/<project_name>/   self-contained CadQuery project
    params.py              dimensions and named parameter sets
    model.py               geometry construction
    __main__.py            build + export entry point
    viewer.py              cq-studio entry point (main() returns {name: model})
    exports/               STEP / STL / DXF outputs (gitignored)
```

Shared utilities live at the repo root only once two projects need them.

## Setup

```sh
brew install uv          # or: curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync
```

## Build a project

```sh
uv run python -m projects.server_rack_shelf
```

The STEP file lands in `projects/server_rack_shelf/exports/`.

## Visualize in the browser

[cq-studio](https://github.com/ccazabon/cq-studio) starts a local server that
renders the model with three.js and hot-reloads on every save to the
`viewer.py` file or anything it imports.

```sh
uv run cq-studio projects/server_rack_shelf/viewer.py
```

Open <http://127.0.0.1:32323/> (port is fixed by the upstream front-end). Edit
`model.py` or `params.py` and the viewer reloads.

A project is wired up by adding `viewer.py` next to `model.py` with a `main()`
function returning a `{name: cq.Workplane}` dict — see
[projects/server_rack_shelf/viewer.py](projects/server_rack_shelf/viewer.py).

## Standards

See [CLAUDE.md](CLAUDE.md).
