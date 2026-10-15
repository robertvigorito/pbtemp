import tomllib
from pathlib import Path

from pbtemp.combine import write_templates_to_cwd
from pbtemp.keyvars import DEFAULTS, get_template_root


def answers(**overrides: str | bool) -> dict[str, str | bool | int]:
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
    written = write_templates_to_cwd(answers(), output_dir=tmp_path)

    assert (tmp_path / "src" / "sample_project" / "main.py").is_file()
    assert (tmp_path / "tests" / "test_main.py").is_file()
    assert not (tmp_path / "nuke").exists()
    assert (tmp_path / "README.md").is_file()
    makefile = (tmp_path / "Makefile").read_text()
    assert "package=sample_project" in makefile
    assert "clean-build:" in makefile
    assert "clean-pyc:" in makefile
    assert "clean-test:" in makefile
    assert "lint-check: lint check" in makefile
    assert "poetry install" in makefile
    project = tomllib.loads((tmp_path / "pyproject.toml").read_text())
    assert project["project"]["name"] == "sample-project"
    assert project["project"]["scripts"] == {"sample-project": "sample_project.main:main"}
    assert len(written) == 7


def test_templates_are_kept_in_external_resource_directory() -> None:
    template_root = get_template_root()

    assert template_root == Path(__file__).parents[1] / "resources" / "templates"
    assert (template_root / "pyproject.toml").is_file()


def test_unselected_optional_files_and_tools_are_omitted(tmp_path: Path) -> None:
    write_templates_to_cwd(
        answers(use_pytest=False, use_ruff=False, use_console_script=False),
        output_dir=tmp_path,
    )

    assert not (tmp_path / "tests").exists()
    project_text = (tmp_path / "pyproject.toml").read_text()
    project = tomllib.loads(project_text)
    assert "scripts" not in project["project"]
    assert "ruff" not in project_text
    assert "pytest" not in project_text


def test_rez_templates_are_copied_only_when_selected(tmp_path: Path) -> None:
    write_templates_to_cwd(answers(use_rez_build=True), output_dir=tmp_path)

    assert (tmp_path / "rez_build" / "package.py").is_file()
    assert (tmp_path / "rez_build" / "rezbuild.py").is_file()
    assert 'env.NUKE_PATH.append("{root}/nuke")' not in (tmp_path / "rez_build" / "package.py").read_text()


def test_nuke_templates_and_rez_path_are_added_when_selected(tmp_path: Path) -> None:
    write_templates_to_cwd(answers(use_nuke=True, use_rez_build=True), output_dir=tmp_path)

    assert (tmp_path / "nuke" / "init.py").is_file()
    assert (tmp_path / "nuke" / "menu.py").is_file()
    assert "sample-project" in (tmp_path / "nuke" / "menu.py").read_text()
    rez_package = (tmp_path / "rez_build" / "package.py").read_text()
    assert 'env.NUKE_PATH.append("{root}/nuke")' in rez_package


def test_existing_files_are_not_overwritten(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("keep me")

    write_templates_to_cwd(answers(), output_dir=tmp_path)

    assert (tmp_path / "README.md").read_text() == "keep me"
    assert (tmp_path / "README1.md").is_file()
