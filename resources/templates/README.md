# {{ project_name }}

{{ description }}

## Getting started

Install the project and its development tools with [uv](https://docs.astral.sh/uv/):

```sh
uv sync
```

{% if use_pytest %}Run the test suite:

```sh
uv run pytest
```

{% endif %}{% if use_console_script %}Run the command-line application:

```sh
uv run {{ command_name }}
```
{% else %}Run the example module:

```sh
uv run python -m {{ package_name }}.main
```
{% endif %}{% if use_mkdocs %}
## Documentation

This project uses [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) with
generated API reference documentation. The site starts in dark mode and its built-in palette control
lets you switch to light mode; your choice is remembered in the browser.

Preview the documentation locally:

```sh
uv run mkdocs serve
```

Build the static site:

```sh
uv run mkdocs build
```
{% endif %}

{% if use_ruff %}## Code formatting

Use Ruff to apply safe lint fixes and format Python files:

```sh
uv run ruff check --fix .
uv run ruff format .
```
{% endif %}

## Template paths

Edit the generated `pbtemp.toml` file (rendered from `resources/pbtemp.toml`) to change where
package, Nuke, and Rez directories are placed. Paths are relative to the project root.
