# pbtemp

`pbtemp` is an interactive command-line tool that generates Python package scaffolds from
maintained project templates. It can start a new project, merge current template configuration into
an existing project, and generate a sample scaffold for checking the templates.

## Install

From a checkout, install the tool and documentation dependencies with
[uv](https://docs.astral.sh/uv/):

```sh
uv sync --group dev
```

The CLI can then be run with `uv run pbtemp`. For an installed `pbtemp` executable, omit `uv run`.

## First command

Create a scaffold in the current working directory:

```sh
uv run pbtemp init
```

The CLI prompts for project metadata and selected tools. A prompt's displayed value is a default;
press Enter to accept it or enter a replacement. MkDocs documentation is enabled by default. See
[Commands](commands.md) for options, behavior, and examples.

## Remembered choices

After a successful `init` or `merge`, the selected options are stored in a user-level configuration
file and reused as defaults on the next run. Inspect or change those choices with
`uv run pbtemp history dump` and `uv run pbtemp history edit`. The [History](history.md) guide
explains precedence, storage, and examples.

## Documentation for generated projects

When MkDocs is enabled, the scaffold includes a home page, API reference, and the Material for
MkDocs theme. It starts in dark mode and provides a built-in **Switch to light mode** / **Switch to
dark mode** control; your selection is remembered in the browser. In the generated project, run
`uv run mkdocs serve` to preview the site or `uv run mkdocs build` to write it under `dist/docs/`.
