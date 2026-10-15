from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from pbtemp import merger_prompt, prompt
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
    assert (project_dir / "nuke" / "init.py").is_file()
    assert (project_dir / "nuke" / "menu.py").is_file()
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


def test_init_options_are_forwarded_as_prompt_defaults(tmp_path: Path, monkeypatch) -> None:
    collected_defaults: dict[str, str | bool | int] = {}

    def fake_collect_answers(*, defaults: dict[str, str | bool | int]) -> dict[str, str | bool | int]:
        collected_defaults.update(defaults)
        return {}

    monkeypatch.setattr(prompt, "_collect_answers", fake_collect_answers)
    monkeypatch.setattr(prompt, "_write_templates", lambda answers, output_dir: [])

    result = CliRunner().invoke(
        prompt.app,
        [
            "init",
            "--output-dir",
            str(tmp_path),
            "--project-name",
            "pbtemp_example",
            "--use-nuke",
        ],
    )

    assert result.exit_code == 0, result.output
    assert collected_defaults == {"project_name": "pbtemp_example", "use_nuke": True}


def test_prompt_uses_supplied_values_as_question_defaults(monkeypatch) -> None:
    class PromptAnswer:
        def __init__(self, value: Any) -> None:
            self.value = value

        def ask(self) -> Any:
            return self.value

    text_defaults: list[str] = []

    def fake_text(_message: str, *, default: str) -> PromptAnswer:
        text_defaults.append(default)
        return PromptAnswer(default)

    def fake_select(_message: str, *, choices: list[str], default: str) -> PromptAnswer:
        assert default in choices
        return PromptAnswer(default)

    def fake_checkbox(_message: str, *, choices: list[Any]) -> PromptAnswer:
        checked_values = [choice.value for choice in choices if choice.checked]
        return PromptAnswer(checked_values)

    monkeypatch.setattr(merger_prompt._questionary, "text", fake_text)
    monkeypatch.setattr(merger_prompt._questionary, "select", fake_select)
    monkeypatch.setattr(merger_prompt._questionary, "checkbox", fake_checkbox)

    answers = merger_prompt.collect_answers(defaults={"project_name": "pbtemp_example", "use_nuke": True})

    assert text_defaults[0] == "pbtemp_example"
    assert answers["package_name"] == "pbtemp_example"
    assert answers["use_nuke"] is True
