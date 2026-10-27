"""Render the selected templates into a destination directory."""

import tomllib as _tomllib
from pathlib import Path as _Path
from typing import Any as _Any

from jinja2 import Environment as _Environment

from pbtemp.keyvars import get_path_map_template_path as _get_path_map_template_path
from pbtemp.keyvars import get_template_paths as _get_template_paths
from pbtemp.keyvars import get_template_root as _get_template_root

_DEFAULT_PATH_MAPPINGS = {
    "package": "src/{package_name}",
    "nuke": "src/nuke",
    "rez_build": "",
}
_OPERATION_TO_TEMPLATE_GROUPS: dict[str, set[str]] = {
    "all": set(),
    "core": {".github", "package"},
    "docs": {"docs", "mkdocs.yml"},
    "tests": {"tests"},
    "nuke": {"nuke"},
    "rez": {"rez_build"},
}


def version_up_on_conflict(path: _Path) -> _Path:
    """Return a non-conflicting path by adding a numeric suffix if needed.

    Args:
        path: Candidate output path.

    Returns:
        Path: The original path if available, otherwise a suffixed path.
    """
    if not path.exists():
        return path
    counter = 1
    counter_path = path
    while counter_path.exists():
        counter_path = path.with_name(f"{path.stem}{counter}{path.suffix}")
        counter += 1
    return counter_path


def write_templates_to_cwd(
    answers: dict[str, _Any],
    prefix: str = "",
    output_dir: _Path | str | None = None,
    config_dir: _Path | str | None = None,
    operation: str = "all",
) -> list[_Path]:
    """Render selected templates into the destination directory.

    Existing files are preserved and receive a numeric suffix on collision.

    Args:
        answers: Values used to render the Jinja templates.
        prefix: Optional prefix added to each generated filename.
        output_dir: Destination directory; defaults to the current directory.
        config_dir: Directory containing optional ``pbtemp.toml`` path mappings.
        operation: Optional migration scope used to filter rendered template groups.

    Returns:
        list[Path]: Paths of all files created.
    """
    environment = _Environment(autoescape=False, keep_trailing_newline=True)
    destination = (_Path(output_dir) if output_dir is not None else _Path.cwd()).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    configuration_root = _Path(config_dir).expanduser().resolve() if config_dir is not None else destination
    path_mappings = get_template_path_mappings(configuration_root)
    template_root = _get_template_root()
    written: list[_Path] = []
    selected_groups = _OPERATION_TO_TEMPLATE_GROUPS.get(operation)
    if selected_groups is None:
        raise ValueError(f"Unknown operation: {operation}")

    for template_path in _get_template_paths():
        relative_path = template_path.relative_to(template_root)
        template_group = relative_path.parts[0]
        if selected_groups and template_group not in selected_groups:
            continue
        if relative_path.parts[0] == "rez_build" and not answers.get("use_rez_build", False):
            continue
        if relative_path.parts[0] == "tests" and not answers.get("use_pytest", False):
            continue
        if relative_path.parts[0] == "nuke" and not answers.get("use_nuke", False):
            continue
        if relative_path.parts[0] == "docs" and not answers.get("use_mkdocs", False):
            continue
        if relative_path == _Path("mkdocs.yml") and not answers.get("use_mkdocs", False):
            continue
        mapped_root = path_mappings.get(relative_path.parts[0])
        if mapped_root is not None:
            mapped_root = mapped_root.replace("{package_name}", str(answers["package_name"]))
            relative_path = _Path(mapped_root, *relative_path.parts[1:])
        if prefix:
            relative_path = relative_path.with_name(f"{prefix}{relative_path.name}")

        output_path = destination / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path = version_up_on_conflict(output_path)
        rendered = environment.from_string(template_path.read_text(encoding="utf-8")).render(**answers)
        output_path.write_text(rendered, encoding="utf-8")
        written.append(output_path)

    # Always ship a project-local path-map config during full/project init runs.
    if operation == "all":
        config_output_path = version_up_on_conflict(destination / "pbtemp.toml")
        rendered_config = environment.from_string(_get_path_map_template_path().read_text(encoding="utf-8")).render(
            **answers
        )
        config_output_path.write_text(rendered_config, encoding="utf-8")
        written.append(config_output_path)

    return written


def get_template_path_mappings(config_dir: _Path) -> dict[str, str]:
    """Load and validate user-defined destination paths for template directories.

    Args:
        config_dir: Directory to check for ``pbtemp.toml``.

    Returns:
        dict[str, str]: Template directory names mapped to relative output paths.

    Raises:
        ValueError: If the configuration file or path mappings are invalid.
    """
    mappings = dict(_DEFAULT_PATH_MAPPINGS)
    config_path = config_dir / "pbtemp.toml"
    if not config_path.is_file():
        return mappings

    try:
        configuration = _tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, _tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Could not read template path configuration at {config_path}: {error}") from error

    raw_mappings = configuration.get("paths", {})
    if not isinstance(raw_mappings, dict):
        raise ValueError("The [paths] section in pbtemp.toml must be a table.")

    for template_dir, output_dir in raw_mappings.items():
        if not isinstance(template_dir, str) or not isinstance(output_dir, str):
            raise ValueError("Template path mappings must use string keys and string values.")
        output_path = _Path(output_dir)
        if output_path.is_absolute() or ".." in output_path.parts:
            raise ValueError(f"Template output path must stay within the project: {output_dir!r}.")
        mappings[template_dir] = output_dir
    return mappings
