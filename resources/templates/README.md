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
{% endif %}
