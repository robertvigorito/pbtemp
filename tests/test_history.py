"""Tests for persistent prompt history."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pbtemp import history, prompt


def test_history_round_trips_known_options(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify known prompt answers persist and unsupported keys are excluded.

    Args:
        tmp_path: Temporary directory for the history file.
        monkeypatch: Pytest fixture for redirecting the history path.

    Returns:
        None: Assertions verify the saved JSON and loaded options.
    """
    history_path = tmp_path / "config" / "history.json"
    monkeypatch.setattr(history, "HISTORY_PATH", history_path)

    saved = history.write_history(
        {
            "project_name": "remembered-project",
            "use_nuke": True,
            "package_name": "remembered_package",
            "unknown": "discard me",
        }
    )

    assert saved is True
    assert history.read_history() == {
        "project_name": "remembered-project",
        "use_nuke": True,
        "package_name": "remembered_package",
    }
    document = json.loads(history_path.read_text(encoding="utf-8"))
    assert document["version"] == 1
    assert "unknown" not in document["options"]
    return None


def test_history_rejects_malformed_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify a corrupt cache is reported instead of being used.

    Args:
        tmp_path: Temporary directory for the history file.
        monkeypatch: Pytest fixture for redirecting the history path.

    Returns:
        None: Assertions check the validation failure.
    """
    history_path = tmp_path / "history.json"
    history_path.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(history, "HISTORY_PATH", history_path)

    with pytest.raises(ValueError, match="not valid JSON"):
        history.read_history()
    return None


def test_history_cli_edit_saves_prompt_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the interactive history editor updates remembered answers.

    Args:
        monkeypatch: Pytest fixture for replacing prompt and storage functions.

    Returns:
        None: Assertions check saved prompt values.
    """
    saved_options: dict[str, str | bool | int] = {}
    monkeypatch.setattr(prompt, "_read_history", lambda: {"project_name": "before"})

    def fake_collect_answers(*, defaults: dict[str, str | bool | int]) -> dict[str, str | bool | int]:
        """Return edited values after verifying current history was loaded.

        Args:
            defaults: Current prompt defaults.

        Returns:
            dict[str, str | bool | int]: Edited values for history storage.
        """
        assert defaults == {"project_name": "before"}
        return {"project_name": "after", "use_nuke": True}

    def fake_write_history(options: dict[str, str | bool | int]) -> bool:
        """Capture values written by the editor.

        Args:
            options: Edited prompt answers.

        Returns:
            bool: Always indicates a successful save.
        """
        saved_options.update(options)
        return True

    monkeypatch.setattr(prompt, "_collect_answers", fake_collect_answers)
    monkeypatch.setattr(prompt, "_write_history", fake_write_history)

    result = CliRunner().invoke(prompt.app, ["history", "edit"])

    assert result.exit_code == 0, result.output
    assert saved_options == {"project_name": "after", "use_nuke": True}
    assert "Saved prompt history" in result.output
    return None
