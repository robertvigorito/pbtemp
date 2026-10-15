"""Template discovery and defaults used by the interactive project generator."""

from functools import lru_cache as _lru_cache
from pathlib import Path as _Path

from jinja2 import Environment as _Environment
from jinja2 import meta as _jinja2_meta

KEY_ASK_ORDER = ["project_name", "version", "description"]
BUILD_BACKEND_KEY = "build_backend"
DEFAULTS: dict[str, str | bool | int] = {
    "project_name": "my-project",
    "version": "0.1.0",
    "description": "A new Python project",
    "requires_python": ">=3.10",
    "line_length": 100,
    "build_backend": "hatchling",
    "use_console_script": True,
    "use_black": False,
    "use_isort": False,
    "use_mypy": False,
    "use_pylint": False,
    "use_pytest": True,
    "use_ruff": True,
    "use_rez_build": False,
    "use_nuke": False,
}
BUILD_BACKENDS = ("hatchling", "uv_build", "setuptools", "flit", "pdm", "poetry")
OPTION_LABELS = {
    "black": "Black formatter",
    "isort": "isort import sorter",
    "mypy": "mypy type checker",
    "pylint": "Pylint linter",
    "pytest": "pytest test framework",
    "ruff": "Ruff linter and formatter",
    "rez_build": "Rez build support",
    "nuke": "Nuke startup and menu support",
    "console_script": "Console command entry point",
}


def get_template_root() -> _Path:
    """Locate the external template resource directory.

    Returns:
        Path: Template root in the checkout or installed package resources.
    """
    module_path = _Path(__file__).resolve()
    for template_root in (
        module_path.parents[2] / "resources" / "templates",
        module_path.parents[1] / "templates",
    ):
        if template_root.is_dir():
            return template_root
    raise FileNotFoundError("Could not find the pbtemp template resources.")


def get_template_paths() -> list[_Path]:
    """List every template file, including nested templates.

    Returns:
        list[Path]: Template paths in stable sorted order.
    """
    return sorted(path for path in get_template_root().rglob("*") if path.is_file())


def get_primary_template_paths() -> list[_Path]:
    """List top-level template files, excluding nested feature sets.

    Returns:
        list[Path]: Paths to top-level templates.
    """
    return sorted(path for path in get_template_root().iterdir() if path.is_file())


@_lru_cache(maxsize=1)
def get_variable_mapping() -> dict[str, str | bool | int | list[str]]:
    """Discover variables referenced by templates and fill known defaults.

    Returns:
        dict[str, str | bool | int | list[str]]: Template variable defaults.
    """
    environment = _Environment()
    variables: set[str] = set()
    for template_path in get_template_paths():
        parsed = environment.parse(template_path.read_text(encoding="utf-8"))
        variables.update(_jinja2_meta.find_undeclared_variables(parsed))

    mapping: dict[str, str | bool | int | list[str]] = {name: DEFAULTS.get(name, "") for name in sorted(variables)}
    return mapping
