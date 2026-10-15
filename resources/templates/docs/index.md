# {{ project_name }}

{{ description }}

## Install

Install the package and its development tools:

```sh
uv sync
```

## Quick start

{% if use_console_script %}Run the command-line application:

```sh
uv run {{ command_name }}
```
{% else %}Run the package module:

```sh
uv run python -m {{ package_name }}.main
```
{% endif %}## Documentation development

Preview the documentation locally with live reload:

```sh
uv run mkdocs serve
```

Build the static site into `dist/docs/`:

```sh
uv run mkdocs build
```
