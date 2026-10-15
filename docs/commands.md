# Terminal commands

Run commands from a terminal in the project directory. If `pbtemp` is not installed as a command,
prefix it with `uv run` while inside the pbtemp checkout. For example, `pbtemp init` becomes
`uv run pbtemp init`.

Get help at any level without starting an interactive prompt:

```sh
pbtemp --help
pbtemp init --help
pbtemp merge --help
pbtemp history --help
```

## `pbtemp init`

Create a new Python project from the bundled templates. By default files are written to the current
working directory. `--output-dir` (short form `-o`) chooses another destination:

```sh
pbtemp init
pbtemp init --output-dir ../new-library
pbtemp init -o /work/new-library
```

The command prompts for project name, version, description, build backend, and optional tools. The
selected options determine which configuration and feature files are generated. If an output file
already exists, the generator keeps it and creates a numbered sibling rather than overwriting it.

### Prefilling prompts with terminal options

Options passed on the command line change the initial values shown by the prompts; they do not skip
the prompts. You may accept or edit any supplied value interactively.

```sh
pbtemp init \
  --output-dir ./widget \
  --project-name widget-tools \
  --version 1.2.0 \
  --description "Utilities for widget projects" \
  --build-backend uv_build \
  --requires-python ">=3.12" \
  --line-length 100
```

Available metadata options:

| Option | Purpose |
| --- | --- |
| `--output-dir`, `-o` | Destination directory; defaults to the current directory. |
| `--project-name NAME` | Default project/distribution name. |
| `--version VERSION` | Default project version. |
| `--description TEXT` | Default short project description. |
| `--build-backend NAME` | Default backend: `hatchling`, `uv_build`, `setuptools`, `flit`, `pdm`, or `poetry`. |
| `--requires-python SPEC` | Default Python compatibility requirement, such as `">=3.12"`. |
| `--line-length N` | Default line length for selected formatter/linter configuration. |

Feature flags also preselect the interactive checklist. Each boolean has a positive and negative
form; the negative form explicitly disables a feature even if history enabled it:

| Enable | Disable | Generated feature |
| --- | --- | --- |
| `--use-console-script` | `--no-use-console-script` | Add the project console entry point. |
| `--use-black` | `--no-use-black` | Configure Black. |
| `--use-isort` | `--no-use-isort` | Configure isort. |
| `--use-mypy` | `--no-use-mypy` | Configure mypy. |
| `--use-mkdocs` | `--no-use-mkdocs` | Add MkDocs config, docs pages, Material for MkDocs, and dev dependencies. Enabled by default. |
| `--use-nuke` | `--no-use-nuke` | Add Nuke startup and menu scripts. |
| `--use-pylint` | `--no-use-pylint` | Configure Pylint. |
| `--use-pytest` | `--no-use-pytest` | Add pytest config and example tests. |
| `--use-ruff` | `--no-use-ruff` | Configure Ruff. |
| `--use-rez-build` | `--no-use-rez-build` | Add Rez package/build support. |

Example: create a project with documentation, tests, and Ruff, but without a console script:

```sh
pbtemp init --project-name widget-tools --use-mkdocs --use-pytest --use-ruff --no-use-console-script
```

`--ignore-history` (also accepted as `--no-history`) ignores saved choices for this invocation.
The command still saves the newly answered choices if generation succeeds. See [History](history.md).

## `pbtemp merge`

Use the latest templates to add missing configuration and files to an existing Python project. Run
it from that project root or supply its path:

```sh
cd ~/work/widget-tools
pbtemp merge

# Or, from any directory:
pbtemp merge --output-dir ~/work/widget-tools
```

The target must contain a valid `pyproject.toml`. Existing project metadata and detected features
are used as prompt defaults. Existing TOML values and the build backend are preserved; missing
configuration and development dependencies are merged in. `.gitignore` entries and missing
Makefile targets are added without replacing existing recipes. Existing source and other conflicting
files are left untouched; absent template files are copied.

Use the same history bypass option as `init` when you want a one-run clean slate:

```sh
pbtemp merge --output-dir . --ignore-history
```

## `pbtemp history`

The `history` command group lets you inspect or interactively edit remembered prompt answers:

```sh
pbtemp history dump
pbtemp history show
pbtemp history edit
```

`dump` and `show` both print the saved options as JSON. `edit` opens the scaffold prompts with current
saved values prefilled and saves the answers for later runs. Details and examples are in
[History](history.md).

## `pbtemp build-temp`

Generate a complete, feature-rich example scaffold under `dist/` to verify bundled templates:

```sh
pbtemp build-temp
```

The command uses fixed sample answers, does not read or write prompt history, and does not build a
wheel. It creates `dist/pbtemp-test-build`; if that directory already exists, it chooses a numbered
sibling such as `dist/pbtemp-test-build-1` rather than overwriting the earlier sample.

## MkDocs in generated projects

MkDocs is selected by default. In a generated project, start a local live-preview server and build
the static site with:

```sh
uv run mkdocs serve
uv run mkdocs build
```

The build output is written to `dist/docs/`. To leave documentation out of a newly created scaffold,
pass `--no-use-mkdocs` to `pbtemp init` or uncheck MkDocs in its feature prompt.
