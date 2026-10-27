"""Tests for merging templates into existing project directories."""

import tomllib
from pathlib import Path

from pbtemp.keyvars import DEFAULTS
from pbtemp.merge import get_existing_project_defaults, merge_project_templates


def test_existing_project_metadata_and_features_become_defaults(tmp_path: Path) -> None:
    """Infer scaffold prompt defaults from project metadata and files.

    Args:
        tmp_path: Temporary project root.

    Returns:
        None: Assertions validate inferred defaults.
    """
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "legacy-app"\nversion = "2.3.4"\n'
        'description = "Existing package"\nrequires-python = ">=3.11"\n'
        'scripts = { legacy = "legacy_import.main:main" }\n'
        '[build-system]\nrequires = ["hatchling"]\n'
        'build-backend = "hatchling.build"\n'
        '[dependency-groups]\ndev = ["pytest>=8", "ruff>=0.5"]\n'
        "[tool.ruff]\nline-length = 88\n",
        encoding="utf-8",
    )
    package_dir = tmp_path / "src" / "legacy_import"
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "nuke").mkdir(parents=True)
    (tmp_path / "docs").mkdir()

    defaults = get_existing_project_defaults(tmp_path)

    assert defaults["project_name"] == "legacy-app"
    assert defaults["package_name"] == "legacy_import"
    assert defaults["command_name"] == "legacy"
    assert defaults["version"] == "2.3.4"
    assert defaults["description"] == "Existing package"
    assert defaults["requires_python"] == ">=3.11"
    assert defaults["build_backend"] == "hatchling"
    assert defaults["use_pytest"] is True
    assert defaults["use_ruff"] is True
    assert defaults["use_nuke"] is True
    assert defaults["use_mkdocs"] is True
    assert defaults["line_length"] == 88

    sparse_defaults = get_existing_project_defaults(tmp_path, include_fallbacks=False)
    assert sparse_defaults["project_name"] == "legacy-app"
    assert sparse_defaults["use_pytest"] is True
    assert "use_black" not in sparse_defaults
    assert "use_rez_build" not in sparse_defaults
    assert sparse_defaults["use_mkdocs"] is True
    return None


def test_merge_detects_pytest_addon_dependencies(tmp_path: Path) -> None:
    """Infer pytest add-on options from existing development dependencies.

    Args:
        tmp_path: Temporary project root.

    Returns:
        None: Assertions verify add-on defaults.
    """
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\n[dependency-groups]\ndev = ["pytest-sugar>=1", "pytest-cov>=6"]\n',
        encoding="utf-8",
    )

    defaults = get_existing_project_defaults(tmp_path, include_fallbacks=False)

    assert defaults["use_pytest_sugar"] is True
    assert defaults["use_coverage"] is True
    return None


def test_merge_preserves_project_values_and_adds_missing_templates(tmp_path: Path) -> None:
    """Merge configuration and absent files without replacing existing source.

    Args:
        tmp_path: Temporary root for the existing project and generated templates.

    Returns:
        None: Assertions verify merged TOML and preserved files.
    """
    original_pyproject = (
        '[project]\nname = "legacy-app"\nversion = "4.2.0"\n'
        'dependencies = ["custom-lib>=1"]\n'
        '[build-system]\nrequires = ["custom-backend"]\n'
        'build-backend = "custom.backend"\n'
        '[tool.custom]\nvalue = "keep"\n'
    )
    (tmp_path / "pyproject.toml").write_text(original_pyproject, encoding="utf-8")
    (tmp_path / "Makefile").write_text(
        "existing make targets\nclean:\n\techo keep-clean-recipe\n",
        encoding="utf-8",
    )
    (tmp_path / ".gitignore").write_text("custom-cache/\n.venv/\n", encoding="utf-8")
    package_dir = tmp_path / "src" / "legacy_import"
    package_dir.mkdir(parents=True)
    existing_main = package_dir / "main.py"
    existing_main.write_text("# keep the user's implementation\n", encoding="utf-8")

    answers: dict[str, str | bool | int] = {
        **DEFAULTS,
        "project_name": "legacy-app",
        "package_name": "legacy_import",
        "command_name": "legacy-app",
        "version": "0.1.0",
        "description": "Template description",
        "build_backend": "hatchling",
        "use_console_script": True,
        "use_black": False,
        "use_isort": False,
        "use_mypy": False,
        "use_pylint": False,
        "use_pytest": True,
        "use_ruff": True,
        "use_rez_build": True,
        "use_nuke": True,
    }

    changed = merge_project_templates(answers=answers, project_dir=tmp_path)

    merged_project = tomllib.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    assert merged_project["project"]["name"] == "legacy-app"
    assert merged_project["project"]["version"] == "4.2.0"
    assert merged_project["project"]["dependencies"] == ["custom-lib>=1"]
    assert merged_project["build-system"]["build-backend"] == "custom.backend"
    assert merged_project["build-system"]["requires"] == ["custom-backend"]
    assert merged_project["tool"]["custom"]["value"] == "keep"
    assert "pytest>=8.0" in merged_project["dependency-groups"]["dev"]
    assert "ruff>=0.5" in merged_project["dependency-groups"]["dev"]
    assert existing_main.read_text(encoding="utf-8") == "# keep the user's implementation\n"
    assert (package_dir / "__init__.py").is_file()
    assert (tmp_path / "tests" / "test_main.py").is_file()
    assert (tmp_path / "package.py").is_file()
    assert (tmp_path / "src" / "nuke" / "init.py").is_file()
    assert "custom-cache/" in (tmp_path / ".gitignore").read_text(encoding="utf-8")
    merged_makefile = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert "existing make targets" in merged_makefile
    assert "echo keep-clean-recipe" in merged_makefile
    assert "clean-build:" in merged_makefile
    assert "build: clean" in merged_makefile
    assert "package=legacy_import" in merged_makefile
    assert tmp_path / "pyproject.toml" in changed
    assert existing_main not in changed
    return None


def test_merge_operation_can_target_only_rez_templates(tmp_path: Path) -> None:
    """Verify merge can add only Rez templates for a focused migration.

    Args:
        tmp_path: Temporary existing-project directory.

    Returns:
        None: Assertions check operation-scoped merge behavior.
    """
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "legacy-app"\nversion = "4.2.0"\n',
        encoding="utf-8",
    )

    answers: dict[str, str | bool | int] = {
        **DEFAULTS,
        "project_name": "legacy-app",
        "package_name": "legacy_import",
        "command_name": "legacy-app",
        "version": "0.1.0",
        "description": "Template description",
        "build_backend": "hatchling",
        "use_console_script": True,
        "use_black": False,
        "use_isort": False,
        "use_mypy": False,
        "use_pylint": False,
        "use_pytest": True,
        "use_ruff": True,
        "use_rez_build": True,
        "use_nuke": False,
    }

    changed = merge_project_templates(answers=answers, project_dir=tmp_path, operation="rez")

    assert (tmp_path / "package.py").is_file()
    assert (tmp_path / "rezbuild.py").is_file()
    assert not (tmp_path / "tests" / "test_main.py").exists()
    assert not (tmp_path / "src" / "legacy_import" / "main.py").exists()
    assert (tmp_path / "package.py") in changed
    return None
