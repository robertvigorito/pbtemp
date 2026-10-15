# pbtemp

`pbtemp` interactively creates Python package scaffolds from configurable templates.

## Install and run

Install the project and development tools with [uv](https://docs.astral.sh/uv/):

```sh
uv sync --group dev
```

Start the interactive scaffold generator:

```sh
uv run pbtemp init
```

To generate a scaffold with documentation enabled (the default), use the MkDocs feature when prompted. In a generated project, preview the docs with `uv run mkdocs serve` and build the static site with `uv run mkdocs build`.

## Features

- Generate a new Python package with `pbtemp init`.
- Add current template configuration to an existing project with `pbtemp merge`.
- Reuse the last selected options through local user history; inspect them with `pbtemp history dump`.
- Generate a complete sample scaffold with `pbtemp build-temp`.

Use `uv run pbtemp init --help` to list scaffold options.
