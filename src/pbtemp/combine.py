"""Render the selected templates into a destination directory."""

import tomllib as _tomllib
from collections.abc import Iterable as _Iterable
from pathlib import Path as _Path
from typing import Any as _Any

from jinja2 import Environment as _Environment

from pbtemp.keyvars import get_path_map_template_path as _get_path_map_template_path
from pbtemp.keyvars import get_template_paths as _get_template_paths
from pbtemp.keyvars import get_template_root as _get_template_root


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
    operation: str | _Iterable[str] = "all",
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
    operations = get_template_operations(configuration_root)
    operation_names = [operation] if isinstance(operation, str) else list(operation)
    if not operation_names:
        raise ValueError("At least one template operation must be selected.")
    unknown_operations = sorted(set(operation_names) - operations.keys())
    if unknown_operations:
        raise ValueError(f"Unknown template operation(s): {', '.join(unknown_operations)}")
    selected_groups = set().union(*(operations[name] for name in operation_names))
    forced_groups = set().union(*(operations[name] for name in operation_names if name != "all"))
    feature_groups = get_template_feature_groups(configuration_root)
    optional_groups = {
        group
        for group in set().union(*feature_groups.values())
        if not any(answers.get(feature, False) for feature, groups in feature_groups.items() if group in groups)
    }

    for template_path in _get_template_paths():
        relative_path = template_path.relative_to(template_root)
        template_group = relative_path.parts[0]
        if selected_groups and template_group not in selected_groups:
            continue
        if template_group not in forced_groups and template_group in optional_groups:
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
    bundled_configuration = _read_template_configuration(_get_path_map_template_path())
    mappings = _validate_path_mappings(bundled_configuration.get("paths", {}))
    config_path = config_dir / "pbtemp.toml"
    if not config_path.is_file():
        return mappings

    project_configuration = _read_template_configuration(config_path)
    mappings.update(_validate_path_mappings(project_configuration.get("paths", {})))
    return mappings


def get_template_operations(config_dir: _Path | None = None) -> dict[str, set[str]]:
    """Load supported template operations from bundled and project TOML configuration.

    Args:
        config_dir: Optional directory containing a project ``pbtemp.toml`` override.

    Returns:
        dict[str, set[str]]: Operation names mapped to template groups.
    """
    bundled_configuration = _read_template_configuration(_get_path_map_template_path())
    operations = _validate_operations(bundled_configuration.get("operations", {}))
    if config_dir is None:
        return operations

    project_config_path = config_dir / "pbtemp.toml"
    if project_config_path.is_file():
        project_configuration = _read_template_configuration(project_config_path)
        operations.update(_validate_operations(project_configuration.get("operations", {})))
    return operations


def get_template_feature_groups(config_dir: _Path | None = None) -> dict[str, set[str]]:
    """Load optional-feature template groups from bundled and project TOML.

    Args:
        config_dir: Optional directory containing project-specific feature mappings.

    Returns:
        dict[str, set[str]]: Feature answer names mapped to template groups.
    """
    bundled_configuration = _read_template_configuration(_get_path_map_template_path())
    features = _validate_operations(bundled_configuration.get("feature_groups", {}))
    if config_dir is None:
        return features

    project_config_path = config_dir / "pbtemp.toml"
    if project_config_path.is_file():
        project_configuration = _read_template_configuration(project_config_path)
        features.update(_validate_operations(project_configuration.get("feature_groups", {})))
    return features


def get_template_group_output_paths(
    config_dir: _Path,
    template_groups: set[str],
    package_name: str,
) -> list[_Path]:
    """Resolve output paths for all templates in the specified template groups.

    Args:
        config_dir: Project directory whose path mappings should be used.
        template_groups: Template root groups to resolve.
        package_name: Import package name used to substitute path placeholders.

    Returns:
        list[Path]: Resolved paths rooted at the project directory.
    """
    template_root = _get_template_root()
    path_mappings = get_template_path_mappings(config_dir)
    output_paths: list[_Path] = []
    for template_path in _get_template_paths():
        relative_path = template_path.relative_to(template_root)
        template_group = relative_path.parts[0]
        if template_group not in template_groups:
            continue
        mapped_root = path_mappings.get(template_group)
        if mapped_root is not None:
            mapped_root = mapped_root.replace("{package_name}", package_name)
            relative_path = _Path(mapped_root, *relative_path.parts[1:])
        output_paths.append(config_dir / relative_path)
    return output_paths


def _read_template_configuration(config_path: _Path) -> dict[str, _Any]:
    """Read a TOML configuration file and ensure its root is a table.

    Args:
        config_path: TOML file to read.

    Returns:
        dict[str, Any]: Parsed TOML configuration.

    Raises:
        ValueError: If the file cannot be read or its TOML is invalid.
    """
    try:
        configuration = _tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, _tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Could not read template configuration at {config_path}: {error}") from error
    if not isinstance(configuration, dict):
        raise ValueError(f"Template configuration at {config_path} must contain a TOML table.")
    return configuration


def _validate_path_mappings(raw_mappings: _Any) -> dict[str, str]:
    """Validate configured template output path mappings.

    Args:
        raw_mappings: Value of the TOML ``[paths]`` table.

    Returns:
        dict[str, str]: Validated template paths.

    Raises:
        ValueError: If mappings are malformed or escape the project directory.
    """
    if not isinstance(raw_mappings, dict):
        raise ValueError("The [paths] section in pbtemp.toml must be a table.")
    mappings: dict[str, str] = {}
    for template_dir, output_dir in raw_mappings.items():
        if not isinstance(template_dir, str) or not isinstance(output_dir, str):
            raise ValueError("Template path mappings must use string keys and string values.")
        output_path = _Path(output_dir)
        if output_path.is_absolute() or ".." in output_path.parts:
            raise ValueError(f"Template output path must stay within the project: {output_dir!r}.")
        mappings[template_dir] = output_dir
    return mappings


def _validate_operations(raw_operations: _Any) -> dict[str, set[str]]:
    """Validate configured operation-to-template-group mappings.

    Args:
        raw_operations: Value of the TOML ``[operations]`` table.

    Returns:
        dict[str, set[str]]: Operation names mapped to selected template groups.

    Raises:
        ValueError: If operation mappings are malformed.
    """
    if not isinstance(raw_operations, dict):
        raise ValueError("The [operations] section in pbtemp.toml must be a table.")
    operations: dict[str, set[str]] = {}
    for operation, groups in raw_operations.items():
        if (
            not isinstance(operation, str)
            or not isinstance(groups, list)
            or not all(isinstance(group, str) for group in groups)
        ):
            raise ValueError("Template operations must map string names to lists of string template groups.")
        operations[operation] = set(groups)
    return operations
