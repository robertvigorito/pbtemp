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

`init` and `merge` remember the last successful answers in the user configuration directory and use them as defaults on later runs. Use `--ignore-history` (or `--no-history`) to skip loading saved answers for one run; the new answers are still saved afterward. Inspect or edit saved answers with:

```sh
pbtemp history dump
pbtemp history edit
```

`pbtemp history show` also displays the saved options. Editing opens the same validated prompts used by scaffold generation.

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

The generated project includes a `pyproject.toml`, README, Makefile, `.gitignore`, shared coding guidance in `.github/copilot-instructions.md`, and a `src`-style import package with documented functions. MkDocs support is enabled by default and adds the Material for MkDocs theme, a home page, and generated API reference. It starts in dark mode and provides a built-in toggle to switch to light mode, remembering the choice in the browser. Use `mkdocs serve` to preview or `mkdocs build` to build the site; disable documentation with `--no-use-mkdocs`. Optional pytest, Rez, and Nuke support can also be included. When Nuke support is selected, it creates startup/menu scripts and adds the package's `nuke` directory to Rez's `NUKE_PATH`. The package name is normalized from the project name, and the console command is configured to call the generated package's `main()` function.

## Development

Run the project's tests with `uv run --group dev pytest`; pytest-sugar formats progress and pytest-cov reports coverage. Check style with `uv run ruff check src tests` and `uv run ruff format --check src tests`. Build and install with `uv build` and `uv pip install .`.
