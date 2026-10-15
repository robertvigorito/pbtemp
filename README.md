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

To verify that every bundled template is copied and the generated project builds, run:

```sh
pbtemp build-temp
```

This copies every template into a complete sample project under `dist/pbtemp-test-build`. It creates a project directory rather than a wheel; if that directory already exists, a numbered sibling is used.

The generated project includes a `pyproject.toml`, README, Makefile, `.gitignore`, a `src`-style import package, and (when selected) pytest and Rez support. Its package name is normalized from the project name, and the console command is configured to call the generated package's `main()` function.

## Development

Run the project's tests with `pytest`. Build and install with `uv build` and `uv pip install .`.
