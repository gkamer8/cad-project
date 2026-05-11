# cad-project

CAD designs authored in [CadQuery](https://github.com/CadQuery/cadquery), kept in source so revisions are diffable and outputs are reproducible.

## Layout

```
projects/<project_name>/   self-contained CadQuery project
    params.py              dimensions and named parameter sets
    model.py               geometry construction
    __main__.py            build + export entry point
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

## Standards

See [CLAUDE.md](CLAUDE.md).
