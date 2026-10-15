"""Tests for the scaffold command-line interface and interactive prompts."""

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from pbtemp import merger_prompt, prompt
from pbtemp.keyvars import get_template_paths


def test_test_build_copies_all_templates_under_dist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the sample command copies every bundled template.

    Args:
        tmp_path: Temporary working directory for generated files.
        monkeypatch: Pytest fixture for changing the current directory.

    Returns:
        None: Assertions check the generated scaffold.
    """
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
    return None


def test_test_build_uses_new_directory_on_repeated_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify repeated sample generations preserve earlier output.

    Args:
        tmp_path: Temporary working directory for generated files.
        monkeypatch: Pytest fixture for changing the current directory.

    Returns:
        None: Assertions check the numbered output directory.
    """
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    assert runner.invoke(prompt.app, ["build-temp"]).exit_code == 0
    result = runner.invoke(prompt.app, ["build-temp"])

    assert result.exit_code == 0, result.output
    assert (tmp_path / "dist" / "pbtemp-test-build-1" / "pyproject.toml").is_file()
    return None


def test_init_options_are_forwarded_as_prompt_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init CLI flags become answer-collection defaults.

    Args:
        tmp_path: Temporary scaffold destination.
        monkeypatch: Pytest fixture for replacing CLI collaborators.

    Returns:
        None: Assertions check the collected defaults.
    """
    collected_defaults: dict[str, str | bool | int] = {}

    def fake_collect_answers(*, defaults: dict[str, str | bool | int]) -> dict[str, str | bool | int]:
        """Record defaults and provide empty sample answers.

        Args:
            defaults: Defaults passed by the init command.

        Returns:
            dict[str, str | bool | int]: Empty answers for this CLI test.
        """
        collected_defaults.update(defaults)
        return {}

    def fake_write_templates(answers: dict[str, Any], output_dir: Path) -> list[Path]:
        """Stub template writing for the init CLI test.

        Args:
            answers: Collected sample answers.
            output_dir: Requested destination directory.

        Returns:
            list[Path]: No paths, since this stub writes no files.
        """
        return []

    monkeypatch.setattr(prompt, "_collect_answers", fake_collect_answers)
    monkeypatch.setattr(prompt, "_write_templates", fake_write_templates)
    monkeypatch.setattr(prompt, "_read_history", lambda: {})
    monkeypatch.setattr(prompt, "_write_history", lambda _answers: True)

    result = CliRunner().invoke(
        prompt.app,
        [
            "init",
            "--output-dir",
            str(tmp_path),
            "--project-name",
            "pbtemp_example",
            "--use-nuke",
            "--use-mkdocs",
            "--use-pytest-sugar",
            "--use-coverage",
        ],
    )

    assert result.exit_code == 0, result.output
    assert collected_defaults == {
        "project_name": "pbtemp_example",
        "use_nuke": True,
        "use_mkdocs": True,
        "use_pytest_sugar": True,
        "use_coverage": True,
    }
    return None


def test_init_uses_history_but_explicit_flags_take_precedence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify saved answers prefill init and explicit options override them.

    Args:
        tmp_path: Temporary scaffold destination.
        monkeypatch: Pytest fixture for replacing CLI collaborators.

    Returns:
        None: Assertions check history and explicit-option precedence.
    """
    collected_defaults: dict[str, str | bool | int] = {}

    def fake_collect_answers(*, defaults: dict[str, str | bool | int]) -> dict[str, str | bool | int]:
        """Record defaults and return sample answers.

        Args:
            defaults: Effective defaults for the prompt.

        Returns:
            dict[str, str | bool | int]: Answers for the CLI stub.
        """
        collected_defaults.update(defaults)
        return {"project_name": "explicit-name", "use_nuke": False}

    monkeypatch.setattr(prompt, "_collect_answers", fake_collect_answers)
    monkeypatch.setattr(prompt, "_write_templates", lambda _answers, output_dir: [])
    monkeypatch.setattr(
        prompt,
        "_read_history",
        lambda: {"project_name": "remembered-name", "use_nuke": True, "line_length": 88},
    )
    monkeypatch.setattr(prompt, "_write_history", lambda _answers: True)

    result = CliRunner().invoke(
        prompt.app,
        ["init", "--output-dir", str(tmp_path), "--project-name", "explicit-name", "--no-use-nuke"],
    )

    assert result.exit_code == 0, result.output
    assert collected_defaults == {
        "project_name": "explicit-name",
        "use_nuke": False,
        "line_length": 88,
    }
    return None


@pytest.mark.parametrize("history_flag", ["--ignore-history", "--no-history"])
def test_init_can_ignore_history_for_one_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    history_flag: str,
) -> None:
    """Verify the ignore-history option skips remembered prompt values.

    Args:
        tmp_path: Temporary scaffold destination.
        monkeypatch: Pytest fixture for replacing CLI collaborators.
        history_flag: CLI option that disables history loading.

    Returns:
        None: Assertions check that history was not read.
    """
    collected_defaults: dict[str, str | bool | int] = {}
    saved_answers: dict[str, str | bool | int] = {}

    def fake_collect_answers(*, defaults: dict[str, str | bool | int]) -> dict[str, str | bool | int]:
        """Record defaults and return sample answers.

        Args:
            defaults: Effective defaults for the prompt.

        Returns:
            dict[str, str | bool | int]: Answers for the CLI stub.
        """
        collected_defaults.update(defaults)
        return {"project_name": "fresh-name"}

    def fail_read_history() -> dict[str, str | bool | int]:
        """Fail if the ignored history is read.

        Returns:
            dict[str, str | bool | int]: Never returns.
        """
        raise AssertionError("history should not be read")

    monkeypatch.setattr(prompt, "_collect_answers", fake_collect_answers)
    monkeypatch.setattr(prompt, "_write_templates", lambda _answers, output_dir: [])
    monkeypatch.setattr(prompt, "_read_history", fail_read_history)

    def fake_write_history(answers: dict[str, str | bool | int]) -> bool:
        """Capture newly entered answers even when history loading is skipped.

        Args:
            answers: New prompt answers.

        Returns:
            bool: Always indicates that the fake save succeeded.
        """
        saved_answers.update(answers)
        return True

    monkeypatch.setattr(prompt, "_write_history", fake_write_history)

    result = CliRunner().invoke(
        prompt.app,
        ["init", "--output-dir", str(tmp_path), history_flag],
    )

    assert result.exit_code == 0, result.output
    assert collected_defaults == {}
    assert saved_answers == {"project_name": "fresh-name"}
    return None


def test_history_dump_displays_saved_options(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the history dump command displays stored values as JSON.

    Args:
        monkeypatch: Pytest fixture for replacing the history reader.

    Returns:
        None: Assertions check command output.
    """
    monkeypatch.setattr(prompt, "_read_history", lambda: {"project_name": "remembered"})

    result = CliRunner().invoke(prompt.app, ["history", "dump"])

    assert result.exit_code == 0, result.output
    assert '"project_name": "remembered"' in result.output
    return None


def test_prompt_uses_supplied_values_as_question_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify supplied values prefill text, select, and checkbox prompts.

    Args:
        monkeypatch: Pytest fixture for replacing questionary prompts.

    Returns:
        None: Assertions check prompt defaults and collected answers.
    """

    class PromptAnswer:
        """Stub a Questionary response with a predetermined answer."""

        def __init__(self, value: Any) -> None:
            """Create a prompt stub with a predetermined answer.

            Args:
                value: Value returned by ``ask``.

            Returns:
                None: The value is stored for the prompt stub.
            """
            self.value: Any = value
            return None

        def ask(self) -> Any:
            """Return the predetermined answer.

            Returns:
                Any: The configured answer.
            """
            return self.value

    text_defaults: list[str] = []

    def fake_text(_message: str, *, default: str) -> PromptAnswer:
        """Build a text prompt stub using its default value.

        Args:
            _message: Prompt text, unused by this test double.
            default: Text value to return from the prompt.

        Returns:
            PromptAnswer: Stub containing the default text.
        """
        text_defaults.append(default)
        return PromptAnswer(default)

    def fake_select(_message: str, *, choices: list[str], default: str) -> PromptAnswer:
        """Build a select prompt stub using its default choice.

        Args:
            _message: Prompt text, unused by this test double.
            choices: Available choices.
            default: Selected default value.

        Returns:
            PromptAnswer: Stub containing the default choice.
        """
        assert default in choices
        return PromptAnswer(default)

    def fake_checkbox(_message: str, *, choices: list[Any]) -> PromptAnswer:
        """Build a checkbox stub from checked options.

        Args:
            _message: Prompt text, unused by this test double.
            choices: Checkbox choices, some of which are checked.

        Returns:
            PromptAnswer: Stub containing the checked option names.
        """
        checked_values = [choice.value for choice in choices if choice.checked]
        return PromptAnswer(checked_values)

    monkeypatch.setattr(merger_prompt._questionary, "text", fake_text)
    monkeypatch.setattr(merger_prompt._questionary, "select", fake_select)
    monkeypatch.setattr(merger_prompt._questionary, "checkbox", fake_checkbox)

    answers = merger_prompt.collect_answers(defaults={"project_name": "pbtemp_example", "use_nuke": True})

    assert text_defaults[0] == "pbtemp_example"
    assert answers["package_name"] == "pbtemp_example"
    assert answers["use_nuke"] is True
    return None


def test_merge_command_updates_existing_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the merge command preserves and extends an existing project.

    Args:
        tmp_path: Temporary existing-project directory.
        monkeypatch: Pytest fixture for supplying non-interactive answers.

    Returns:
        None: Assertions check the command output and merged project files.
    """
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "existing-app"\nversion = "2.0.0"\n',
        encoding="utf-8",
    )
    sample_answers: dict[str, str | bool | int] = {
        "project_name": "existing-app",
        "package_name": "existing_app",
        "command_name": "existing-app",
        "version": "0.1.0",
        "description": "Existing project",
        "requires_python": ">=3.12",
        "line_length": 100,
        "build_backend": "hatchling",
        "use_console_script": False,
        "use_black": False,
        "use_isort": False,
        "use_mypy": False,
        "use_nuke": False,
        "use_pylint": False,
        "use_pytest": True,
        "use_ruff": True,
        "use_rez_build": False,
    }

    def fake_collect_answers(*, defaults: dict[str, str | bool | int]) -> dict[str, str | bool | int]:
        """Return sample answers while checking metadata was inferred.

        Args:
            defaults: Defaults inferred from the existing project.

        Returns:
            dict[str, str | bool | int]: Answers for a test package merge.
        """
        assert defaults["project_name"] == "existing-app"
        return sample_answers

    monkeypatch.setattr(prompt, "_collect_answers", fake_collect_answers)
    monkeypatch.setattr(prompt, "_read_history", lambda: {})
    monkeypatch.setattr(prompt, "_write_history", lambda _answers: True)

    result = CliRunner().invoke(prompt.app, ["merge", "--output-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    assert "Merged template configuration" in result.output
    assert (tmp_path / "src" / "existing_app" / "main.py").is_file()
    assert (tmp_path / "tests" / "test_main.py").is_file()
    return None
