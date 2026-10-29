"""Tests for rendering and validating generated project scaffolds."""

import tomllib
from pathlib import Path

from pbtemp.combine import write_templates_to_cwd
from pbtemp.keyvars import DEFAULTS, get_path_map_template_path, get_template_root


def answers(**overrides: str | bool | int) -> dict[str, str | bool | int]:
    """Build sample answer values for scaffold tests.

    Args:
        **overrides: Values that replace the common sample answers.

    Returns:
        dict[str, str | bool | int]: Complete scaffold answers.
    """
    values: dict[str, str | bool | int] = dict(DEFAULTS)
    values.update(
        {
            "project_name": "sample-project",
            "package_name": "sample_project",
            "command_name": "sample-project",
            "description": "A sample package",
            "version": "1.2.3",
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
    )
    values.update(overrides)
    return values


def test_generates_project_layout_and_valid_pyproject(tmp_path: Path) -> None:
    """Verify generated files, Makefile, and project metadata.

    Args:
        tmp_path: Temporary destination for the generated scaffold.

    Returns:
        None: Assertions check project layout and metadata.
    """
    written = write_templates_to_cwd(answers(), output_dir=tmp_path)

    assert (tmp_path / "src" / "sample_project" / "main.py").is_file()
    assert (tmp_path / "tests" / "test_main.py").is_file()
    assert not (tmp_path / "nuke").exists()
    assert (tmp_path / ".github" / "copilot-instructions.md").is_file()
    generated_main = (tmp_path / "src" / "sample_project" / "main.py").read_text()
    assert "Returns:" in generated_main
    assert "return 0" in generated_main
    assert (tmp_path / "README.md").is_file()
    assert (tmp_path / "mkdocs.yml").is_file()
    assert (tmp_path / "docs" / "index.md").is_file()
    assert (tmp_path / "docs" / "api.md").is_file()
    makefile = (tmp_path / "Makefile").read_text()
    assert "package=sample_project" in makefile
    assert "clean-build:" in makefile
    assert "clean-pyc:" in makefile
    assert "clean-test:" in makefile
    assert "lint-check: lint check" in makefile
    assert "uv sync" in makefile
    assert "uv run pytest ./tests" in makefile
    assert "uv run ruff check ." in makefile
    assert "uv run black --check ." not in makefile
    assert "uv run isort" not in makefile
    assert "uv run mypy" not in makefile
    assert "uv run pylint" not in makefile
    assert "poetry" not in makefile
    assert "pip install" not in makefile
    project = tomllib.loads((tmp_path / "pyproject.toml").read_text())
    assert project["project"]["name"] == "sample-project"
    assert project["project"]["requires-python"] == ">=3.10"
    assert project["project"]["scripts"] == {"sample-project": "sample_project.main:main"}
    development_dependencies = project["dependency-groups"]["dev"]
    assert "mkdocs>=1.6,<2" in development_dependencies
    assert "mkdocs-material>=9.6" in development_dependencies
    assert "name: material" in (tmp_path / "mkdocs.yml").read_text()
    assert "Material for MkDocs" in (tmp_path / "README.md").read_text()
    assert project["tool"]["ruff"]["line-length"] == 120
    assert "ruff check --fix ." in (tmp_path / "Makefile").read_text()
    assert "ruff format ." in (tmp_path / "Makefile").read_text()
    assert "120-character" in (tmp_path / ".github" / "copilot-instructions.md").read_text()
    assert project["tool"]["ruff"]["line-length"] == 120
    assert "pytest-sugar" not in development_dependencies
    assert "pytest-cov" not in development_dependencies
    assert not (tmp_path / "pbtemp.toml").exists()
    assert len(written) == 11
    return None


def test_mkdocs_templates_are_optional_and_configured(tmp_path: Path) -> None:
    """Verify MkDocs templates and dependencies are included when selected.

    Args:
        tmp_path: Temporary destination for generated files.

    Returns:
        None: Assertions check MkDocs files and dependency configuration.
    """
    write_templates_to_cwd(answers(use_mkdocs=True), output_dir=tmp_path)

    project = tomllib.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    development_dependencies = project["dependency-groups"]["dev"]
    assert "mkdocs>=1.6,<2" in development_dependencies
    assert "mkdocs-material>=9.6" in development_dependencies
    assert "mkdocstrings[python]>=0.27" in development_dependencies
    assert (tmp_path / "mkdocs.yml").is_file()
    config = (tmp_path / "mkdocs.yml").read_text()
    assert "name: material" in config
    assert "scheme: slate" in config
    assert "Switch to light mode" in config
    assert (tmp_path / "docs" / "index.md").is_file()
    assert "::: sample_project.main" in (tmp_path / "docs" / "api.md").read_text()
    assert "uv run mkdocs serve" in (tmp_path / "docs" / "index.md").read_text()
    return None


def test_python_requirement_can_be_customized(tmp_path: Path) -> None:
    """Verify the selected Python requirement is written to project metadata.

    Args:
        tmp_path: Temporary destination for generated files.

    Returns:
        None: Assertions check the generated Python requirement.
    """
    write_templates_to_cwd(answers(requires_python=">=3.12"), output_dir=tmp_path)

    project = tomllib.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["project"]["requires-python"] == ">=3.12"
    return None


def test_pytest_sugar_and_coverage_are_optional(tmp_path: Path) -> None:
    """Verify selected pytest add-ons are installed and coverage is configured.

    Args:
        tmp_path: Temporary destination for generated files.

    Returns:
        None: Assertions check selected dependencies and pytest options.
    """
    write_templates_to_cwd(
        answers(use_pytest_sugar=True, use_coverage=True),
        output_dir=tmp_path,
    )

    project = tomllib.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = project["dependency-groups"]["dev"]
    assert "pytest>=8.0" in dependencies
    assert "pytest-sugar>=1.0" in dependencies
    assert "pytest-cov>=6.0" in dependencies
    pytest_options = project["tool"]["pytest"]["ini_options"]["addopts"]
    assert "--cov=sample_project" in pytest_options
    assert "--cov-report=term-missing" in pytest_options
    assert "--cov-report=html" in pytest_options
    makefile = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert "uv run pytest ./tests" in makefile
    assert "Coverage HTML report is available" in makefile
    return None


def test_line_length_is_shared_by_selected_formatters_and_linters(tmp_path: Path) -> None:
    """Verify the selected line length configures each enabled formatter and linter.

    Args:
        tmp_path: Temporary destination for generated files.

    Returns:
        None: Assertions check all supported line-length settings.
    """
    write_templates_to_cwd(
        answers(
            line_length=88,
            use_black=True,
            use_isort=True,
            use_pylint=True,
            use_ruff=True,
            use_mypy=True,
        ),
        output_dir=tmp_path,
    )

    project = tomllib.loads((tmp_path / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["tool"]["black"]["line-length"] == 88
    assert project["tool"]["isort"]["line_length"] == 88
    assert project["tool"]["pylint"]["format"]["max-line-length"] == 88
    assert project["tool"]["ruff"]["line-length"] == 88
    makefile = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert "uv run black --check ." in makefile
    assert "uv run isort --check-only --profile black ." in makefile
    assert "uv run pylint --exit-zero src" in makefile
    assert "uv run mypy --ignore-missing-imports src" in makefile
    assert "uv run black ." in makefile
    assert "uv run isort --profile black ." in makefile
    return None


def test_project_path_configuration_overrides_template_locations(tmp_path: Path) -> None:
    """Verify project configuration controls template subdirectory destinations.

    Args:
        tmp_path: Temporary destination containing a custom pbtemp config.

    Returns:
        None: Assertions check custom output locations.
    """
    (tmp_path / "pbtemp.toml").write_text(
        '[paths]\npackage = "lib/{package_name}"\nnuke = "tools/nuke"\nrez_build = "build/rez"\n',
        encoding="utf-8",
    )

    write_templates_to_cwd(
        answers(use_nuke=True, use_rez_build=True),
        output_dir=tmp_path,
    )

    assert (tmp_path / "lib" / "sample_project" / "main.py").is_file()
    assert (tmp_path / "tools" / "nuke" / "init.py").is_file()
    assert (tmp_path / "build" / "rez" / "package.py").is_file()
    assert (tmp_path / "pbtemp.toml").is_file()
    assert not (tmp_path / "pbtemp1.toml").exists()
    return None


def test_project_configuration_can_define_template_operations(tmp_path: Path) -> None:
    """Verify custom operations in pbtemp.toml select their configured template groups.

    Args:
        tmp_path: Temporary destination containing custom template configuration.

    Returns:
        None: Assertions verify that only the configured template group is rendered.
    """
    (tmp_path / "pbtemp.toml").write_text(
        '[operations]\nchecks = ["tests"]\n',
        encoding="utf-8",
    )

    write_templates_to_cwd(answers(), output_dir=tmp_path, operation="checks")

    assert (tmp_path / "tests" / "test_main.py").is_file()
    assert not (tmp_path / "Makefile").exists()
    return None


def test_templates_are_kept_in_external_resource_directory() -> None:
    """Verify templates are outside the Python package source.

    Returns:
        None: Assertions check the resource location.
    """
    template_root = get_template_root()
    path_map_template = get_path_map_template_path()

    assert template_root == Path(__file__).parents[1] / "resources" / "templates"
    assert (template_root / "pyproject.toml").is_file()
    assert path_map_template == Path(__file__).parents[1] / "resources" / "pbtemp.toml"
    assert path_map_template.is_file()
    return None


def test_unselected_optional_files_and_tools_are_omitted(tmp_path: Path) -> None:
    """Verify optional files and settings are omitted when disabled.

    Args:
        tmp_path: Temporary destination for the generated scaffold.

    Returns:
        None: Assertions check omitted features.
    """
    write_templates_to_cwd(
        answers(
            use_pytest=False,
            use_ruff=False,
            use_console_script=False,
            use_mkdocs=False,
        ),
        output_dir=tmp_path,
    )

    assert not (tmp_path / "tests").exists()
    project_text = (tmp_path / "pyproject.toml").read_text()
    project = tomllib.loads(project_text)
    assert "scripts" not in project["project"]
    assert "ruff" not in project_text
    assert "pytest" not in project_text
    assert not (tmp_path / "mkdocs.yml").exists()
    assert not (tmp_path / "docs").exists()
    makefile = (tmp_path / "Makefile").read_text(encoding="utf-8")
    assert "uv run mkdocs build" not in makefile
    assert "uv run mkdocs serve" not in makefile
    return None


def test_rez_templates_are_copied_only_when_selected(tmp_path: Path) -> None:
    """Verify Rez templates are included only when requested.

    Args:
        tmp_path: Temporary destination for the generated scaffold.

    Returns:
        None: Assertions check Rez file and Nuke path selection.
    """
    write_templates_to_cwd(answers(use_rez_build=True), output_dir=tmp_path)

    assert (tmp_path / "package.py").is_file()
    assert (tmp_path / "rezbuild.py").is_file()
    assert 'env.NUKE_PATH.append("{root}/src/nuke")' not in (tmp_path / "package.py").read_text()
    return None


def test_nuke_templates_and_rez_path_are_added_when_selected(tmp_path: Path) -> None:
    """Verify Nuke scripts and the Rez path are included when enabled.

    Args:
        tmp_path: Temporary destination for the generated scaffold.

    Returns:
        None: Assertions check Nuke integration files and environment setup.
    """
    write_templates_to_cwd(answers(use_nuke=True, use_rez_build=True), output_dir=tmp_path)

    assert (tmp_path / "src" / "nuke" / "init.py").is_file()
    assert (tmp_path / "src" / "nuke" / "menu.py").is_file()
    assert "sample-project" in (tmp_path / "src" / "nuke" / "menu.py").read_text()
    rez_package = (tmp_path / "package.py").read_text()
    assert 'env.NUKE_PATH.append("{root}/src/nuke")' in rez_package
    assert "noqa: F821" in rez_package
    assert "noqa: I001" in (tmp_path / "src" / "nuke" / "menu.py").read_text()
    return None


def test_existing_files_are_not_overwritten(tmp_path: Path) -> None:
    """Verify generated content uses suffixed paths on collisions.

    Args:
        tmp_path: Temporary destination containing a pre-existing file.

    Returns:
        None: Assertions check original and generated file contents.
    """
    (tmp_path / "README.md").write_text("keep me")

    write_templates_to_cwd(answers(), output_dir=tmp_path)

    assert (tmp_path / "README.md").read_text() == "keep me"
    assert (tmp_path / "README1.md").is_file()
    return None


def test_operation_filter_can_limit_generation_to_rez_templates(tmp_path: Path) -> None:
    """Verify operation filtering can generate only Rez-related templates.

    Args:
        tmp_path: Temporary destination for generated files.

    Returns:
        None: Assertions verify operation-scoped generation output.
    """
    write_templates_to_cwd(
        answers(use_rez_build=True, use_nuke=False),
        output_dir=tmp_path,
        operation="rez",
    )

    assert (tmp_path / "package.py").is_file()
    assert (tmp_path / "rezbuild.py").is_file()
    assert not (tmp_path / "pyproject.toml").exists()
    assert not (tmp_path / "pbtemp.toml").exists()
    return None
