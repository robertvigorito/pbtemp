"""Merge generated scaffold files and configuration into an existing project."""

import re as _re
import tomllib as _tomllib
from collections.abc import Mapping
from copy import deepcopy as _deepcopy
from pathlib import Path as _Path
from tempfile import TemporaryDirectory as _TemporaryDirectory
from typing import Any as _Any

import tomlkit as _tomlkit
from tomlkit.items import Array as _Array
from tomlkit.items import InlineTable as _InlineTable
from tomlkit.items import Table as _Table

from pbtemp.combine import write_templates_to_cwd as _write_templates
from pbtemp.keyvars import DEFAULTS as _DEFAULTS

_BACKEND_NAMES = {
    "hatchling.build": "hatchling",
    "uv_build": "uv_build",
    "setuptools.build_meta": "setuptools",
    "flit_core.buildapi": "flit",
    "pdm.backend": "pdm",
    "poetry.core.masonry.api": "poetry",
}
_FEATURE_TO_PACKAGE = {
    "black": "use_black",
    "isort": "use_isort",
    "mypy": "use_mypy",
    "pylint": "use_pylint",
    "pytest": "use_pytest",
    "ruff": "use_ruff",
}


def get_existing_project_defaults(project_dir: _Path) -> dict[str, str | bool | int]:
    """Infer scaffold prompt defaults from an existing Python project.

    Args:
        project_dir: Root directory of the existing project.

    Returns:
        dict[str, str | bool | int]: Defaults inferred from project metadata and files.

    Raises:
        FileNotFoundError: If the project has no pyproject.toml.
        ValueError: If the project's TOML metadata is invalid.
    """
    project_dir = project_dir.expanduser().resolve()
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.is_file():
        raise FileNotFoundError(f"No pyproject.toml found in {project_dir}.")

    try:
        project_data = _tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except _tomllib.TOMLDecodeError as error:
        raise ValueError(f"Could not parse {pyproject_path}: {error}") from error

    metadata = project_data.get("project", {})
    project_name = str(metadata.get("name", project_dir.name))
    package_name = _find_package_name(project_dir, project_name)
    build_system = project_data.get("build-system", {})
    build_backend = _BACKEND_NAMES.get(
        str(build_system.get("build-backend", "")),
        str(_DEFAULTS["build_backend"]),
    )
    tool_config = project_data.get("tool", {})
    dev_packages = _collect_dev_packages(project_data)

    defaults: dict[str, str | bool | int] = {
        **_DEFAULTS,
        "project_name": project_name,
        "package_name": package_name,
        "command_name": _find_command_name(project_data, project_name),
        "version": str(metadata.get("version", _DEFAULTS["version"])),
        "description": str(metadata.get("description", _DEFAULTS["description"])),
        "requires_python": str(metadata.get("requires-python", _DEFAULTS["requires_python"])),
        "build_backend": build_backend,
        "use_console_script": bool(metadata.get("scripts", {})),
        "use_rez_build": (project_dir / "rez_build").is_dir(),
        "use_nuke": (project_dir / "nuke").is_dir(),
    }
    for package, option in _FEATURE_TO_PACKAGE.items():
        defaults[option] = package in dev_packages or package in tool_config

    line_lengths = (
        tool_config.get("ruff", {}).get("line-length"),
        tool_config.get("black", {}).get("line-length"),
        tool_config.get("isort", {}).get("line_length"),
    )
    defaults["line_length"] = next(
        (int(length) for length in line_lengths if length is not None),
        int(_DEFAULTS["line_length"]),
    )
    defaults["use_pytest"] = bool(defaults["use_pytest"] or (project_dir / "tests").is_dir())
    defaults["use_nuke"] = bool(defaults["use_nuke"])
    defaults["use_rez_build"] = bool(defaults["use_rez_build"])
    return defaults


def merge_project_templates(
    answers: dict[str, str | bool | int],
    project_dir: _Path,
) -> list[_Path]:
    """Merge rendered templates into an existing project without overwriting source.

    The existing pyproject.toml is merged recursively: existing scalar settings take
    precedence, while missing keys and new list values from the template are added.
    Other conflicting files are preserved; missing files are copied and .gitignore
    entries are appended when absent.

    Args:
        answers: Values used to render the selected templates.
        project_dir: Root directory of the existing project.

    Returns:
        list[Path]: Paths added or updated by the merge.

    Raises:
        FileNotFoundError: If the existing project's pyproject.toml is missing.
        ValueError: If either existing or generated TOML is invalid.
    """
    destination = project_dir.expanduser().resolve()
    if not (destination / "pyproject.toml").is_file():
        raise FileNotFoundError(f"No pyproject.toml found in {destination}.")

    destination.mkdir(parents=True, exist_ok=True)
    changed: list[_Path] = []
    with _TemporaryDirectory(prefix="pbtemp-merge-") as temporary_directory:
        template_root = _Path(temporary_directory)
        rendered_files = _write_templates(answers, output_dir=template_root)
        for rendered_path in rendered_files:
            relative_path = rendered_path.relative_to(template_root)
            existing_path = destination / relative_path
            existing_path.parent.mkdir(parents=True, exist_ok=True)

            if relative_path == _Path("pyproject.toml"):
                if _merge_pyproject(existing_path, rendered_path):
                    changed.append(existing_path)
            elif relative_path == _Path("Makefile") and existing_path.exists():
                if _merge_makefile(existing_path, rendered_path):
                    changed.append(existing_path)
            elif relative_path == _Path(".gitignore") and existing_path.exists():
                if _merge_gitignore(existing_path, rendered_path):
                    changed.append(existing_path)
            elif not existing_path.exists():
                existing_path.write_bytes(rendered_path.read_bytes())
                changed.append(existing_path)

    return changed


def _find_package_name(project_dir: _Path, project_name: str) -> str:
    """Find the import package used by an existing src-layout project.

    Args:
        project_dir: Root directory of the project.
        project_name: Distribution name used as a normalization fallback.

    Returns:
        str: Import package name for generated template references.
    """
    source_root = project_dir / "src"
    normalized_name = project_name.replace("-", "_").replace(".", "_").lower()
    if (source_root / normalized_name / "__init__.py").is_file():
        return normalized_name
    if source_root.is_dir():
        package_dirs = sorted(path.name for path in source_root.iterdir() if (path / "__init__.py").is_file())
        if package_dirs:
            return package_dirs[0]
    return normalized_name


def _find_command_name(project_data: dict[str, _Any], project_name: str) -> str:
    """Find an existing console script name or normalize the project name.

    Args:
        project_data: Parsed existing pyproject data.
        project_name: Distribution name used as a fallback.

    Returns:
        str: Existing or normalized console command name.
    """
    scripts = project_data.get("project", {}).get("scripts", {})
    if scripts:
        return str(next(iter(scripts)))
    return project_name.replace("_", "-").lower()


def _collect_dev_packages(project_data: dict[str, _Any]) -> set[str]:
    """Collect package names from dependency groups and legacy dev dependencies.

    Args:
        project_data: Parsed existing pyproject data.

    Returns:
        set[str]: Normalized development dependency names.
    """
    dependency_groups = project_data.get("dependency-groups", {})
    dev_requirements = [str(item) for item in dependency_groups.get("dev", [])]
    dev_requirements.extend(
        str(item) for item in project_data.get("tool", {}).get("uv", {}).get("dev-dependencies", [])
    )
    return {_re.split(r"[<>=!~;\[]", requirement, maxsplit=1)[0].strip().lower() for requirement in dev_requirements}


def _merge_pyproject(existing_path: _Path, template_path: _Path) -> bool:
    """Add absent template keys and list values to an existing TOML document.

    Args:
        existing_path: Existing destination pyproject.toml.
        template_path: Rendered template pyproject.toml.

    Returns:
        bool: ``True`` when the destination document was changed.

    Raises:
        ValueError: If either TOML document cannot be parsed.
    """
    try:
        existing_document = _tomlkit.parse(existing_path.read_text(encoding="utf-8"))
        template_document = _tomlkit.parse(template_path.read_text(encoding="utf-8"))
    except _tomlkit.exceptions.ParseError as error:
        raise ValueError(f"Could not merge TOML configuration: {error}") from error

    changed = _merge_table(existing_document, template_document)
    if changed:
        existing_path.write_text(_tomlkit.dumps(existing_document), encoding="utf-8")
    return changed


def _merge_table(existing: _Table | _InlineTable | _Any, template: Mapping[str, _Any]) -> bool:
    """Merge a template mapping into an existing TOML table recursively.

    Args:
        existing: Mutable TOML table to update.
        template: Template values to add.

    Returns:
        bool: ``True`` when any value was added.
    """
    changed = False
    for key, template_value in template.items():
        if key not in existing:
            existing[key] = _deepcopy(template_value)
            changed = True
            continue

        existing_value = existing[key]
        if key == "build-system":
            continue
        if isinstance(existing_value, (_Table, _InlineTable)) and isinstance(template_value, Mapping):
            changed = _merge_table(existing_value, template_value) or changed
        elif isinstance(existing_value, _Array) and isinstance(template_value, _Array):
            current_values = [item.unwrap() for item in existing_value]
            for item in template_value:
                if item.unwrap() not in current_values:
                    existing_value.append(_deepcopy(item))
                    current_values.append(item.unwrap())
                    changed = True
    return changed


def _merge_gitignore(existing_path: _Path, template_path: _Path) -> bool:
    """Append template ignore patterns not already present.

    Args:
        existing_path: Existing .gitignore file.
        template_path: Rendered .gitignore template.

    Returns:
        bool: ``True`` when new ignore patterns were appended.
    """
    existing_text = existing_path.read_text(encoding="utf-8")
    existing_lines = set(existing_text.splitlines())
    additions = [
        line for line in template_path.read_text(encoding="utf-8").splitlines() if line and line not in existing_lines
    ]
    if not additions:
        return False

    separator = "" if not existing_text or existing_text.endswith("\n") else "\n"
    existing_path.write_text(
        f"{existing_text}{separator}{'\n'.join(additions)}\n",
        encoding="utf-8",
    )
    return True


def _merge_makefile(existing_path: _Path, template_path: _Path) -> bool:
    """Add template Makefile targets missing from an existing Makefile.

    Existing target recipes and variables are retained. Template prerequisites are
    added to an existing ``clean`` target, while missing target rules are appended.

    Args:
        existing_path: Existing destination Makefile.
        template_path: Rendered Makefile template.

    Returns:
        bool: ``True`` when target rules or phony declarations were added.
    """
    existing_text = existing_path.read_text(encoding="utf-8")
    template_text = template_path.read_text(encoding="utf-8")
    existing_lines = existing_text.splitlines()
    template_lines = template_text.splitlines()
    target_pattern = _re.compile(r"^([A-Za-z0-9_.%-]+)\s*:")
    existing_targets = {
        match.group(1)
        for line in existing_lines
        if (match := target_pattern.match(line)) is not None and match.group(1) != ".PHONY"
    }
    changed = False

    template_phony = next((line for line in template_lines if line.startswith(".PHONY:")), None)
    if template_phony is not None:
        phony_targets = template_phony.partition(":")[2].split()
        phony_index = next(
            (index for index, line in enumerate(existing_lines) if line.startswith(".PHONY:")),
            None,
        )
        if phony_index is None:
            existing_lines.append(template_phony)
            changed = True
        else:
            current_phony = existing_lines[phony_index].partition(":")[2].split()
            merged_phony = list(dict.fromkeys([*current_phony, *phony_targets]))
            merged_line = f".PHONY: {' '.join(merged_phony)}"
            if existing_lines[phony_index] != merged_line:
                existing_lines[phony_index] = merged_line
                changed = True

    template_package = next((line for line in template_lines if line.startswith("package=")), None)
    if template_package is not None and not any(line.startswith("package=") for line in existing_lines):
        existing_lines.insert(0, template_package)
        changed = True

    clean_template = next((line for line in template_lines if line.startswith("clean:")), None)
    if clean_template is not None:
        clean_index = next(
            (index for index, line in enumerate(existing_lines) if line.startswith("clean:")),
            None,
        )
        if clean_index is not None:
            current_line = existing_lines[clean_index]
            current_dependencies = current_line.partition(":")[2].split("#", maxsplit=1)[0].split()
            template_dependencies = clean_template.partition(":")[2].split("#", maxsplit=1)[0].split()
            merged_dependencies = list(dict.fromkeys([*current_dependencies, *template_dependencies]))
            comment = current_line.partition("#")[2]
            merged_line = f"clean: {' '.join(merged_dependencies)}"
            if comment:
                merged_line = f"{merged_line} #{comment}"
            if current_line != merged_line:
                existing_lines[clean_index] = merged_line
                changed = True

    for index, line in enumerate(template_lines):
        match = target_pattern.match(line)
        if match is None or match.group(1) == ".PHONY" or match.group(1) in existing_targets:
            continue
        rule_lines = [line]
        next_index = index + 1
        while next_index < len(template_lines):
            next_line = template_lines[next_index]
            if target_pattern.match(next_line) or (next_line and not next_line[0].isspace()):
                break
            rule_lines.append(next_line)
            next_index += 1
        while rule_lines and not rule_lines[-1]:
            rule_lines.pop()
        if existing_lines and existing_lines[-1]:
            existing_lines.append("")
        existing_lines.extend(rule_lines)
        existing_targets.add(match.group(1))
        changed = True

    if changed:
        existing_path.write_text("\n".join(existing_lines) + "\n", encoding="utf-8")
    return changed
