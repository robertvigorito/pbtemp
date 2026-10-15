from pathlib import Path

from typer.testing import CliRunner

import pbtemp.prompt as prompt
from pbtemp.keyvars import get_template_paths


def test_test_build_copies_all_templates_under_dist(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(prompt.app, ["build-temp"])

    assert result.exit_code == 0, result.output
    project_dir = tmp_path / "dist" / "pbtemp-test-build"
    copied_files = [path for path in project_dir.rglob("*") if path.is_file()]
    assert len(copied_files) == len(get_template_paths())
    assert (project_dir / "pyproject.toml").is_file()
    assert (project_dir / "src" / "pbtemp_test_build" / "main.py").is_file()
    assert (project_dir / "rez_build" / "package.py").is_file()
    assert (project_dir / "tests" / "test_main.py").is_file()
    assert not list(project_dir.rglob("*.whl"))
    assert "Copied all" in result.output
    assert "Complete sample project scaffold created" in result.output


def test_test_build_uses_new_directory_on_repeated_runs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    assert runner.invoke(prompt.app, ["build-temp"]).exit_code == 0
    result = runner.invoke(prompt.app, ["build-temp"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "dist" / "pbtemp-test-build-1" / "pyproject.toml").is_file()
