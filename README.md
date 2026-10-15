# pbtemp

`pbtemp` interactively creates a Python package scaffold from the templates bundled with the tool. It asks for project metadata, a build backend, and optional developer tools, then renders only the selected features into the destination directory. Existing files are preserved and receive a numeric suffix rather than being overwritten.

The scaffold files are maintained separately from the Python source in `resources/templates` and included as wheel resources when the tool is built.

## Usage

Install the project, then run:

```sh
pbtemp init
```

The generator writes into the current directory by default. Choose another destination with `--output-dir` / `-o`:

```sh
pbtemp init --output-dir ../new-project
```

You can prefill interactive answers with options, including feature flags:

```sh
pbtemp init --project-name pbtemp_example --use-nuke
```

These values become the defaults shown in the prompts; the answers can still be changed interactively. Boolean options also support `--no-use-...` forms.

Merge template configuration into an existing project with:

```sh
pbtemp merge --output-dir .
```

The merge command uses existing project metadata and detected features as prompt defaults. It preserves existing TOML values and build-system configuration, adds missing template settings and development dependencies, extends `.gitignore` and existing Makefiles without replacing their targets, and only copies other files that do not already exist.

To verify that every bundled template is copied and create a complete sample project, run:

```sh
pbtemp build-temp
```

This copies every template into a complete sample project under `dist/pbtemp-test-build`. It creates a project directory rather than a wheel; if that directory already exists, a numbered sibling is used.

The generated project includes a `pyproject.toml`, README, Makefile, `.gitignore`, shared coding guidance in `.github/copilot-instructions.md`, and a `src`-style import package with documented functions. Optional pytest, Rez, and Nuke support can also be included. When Nuke support is selected, it creates startup/menu scripts and adds the package's `nuke` directory to Rez's `NUKE_PATH`. The package name is normalized from the project name, and the console command is configured to call the generated package's `main()` function.

## Development

Run the project's tests with `uv run --group dev pytest`. Check style with `uv run ruff check src tests` and `uv run ruff format --check src tests`. Build and install with `uv build` and `uv pip install .`.
