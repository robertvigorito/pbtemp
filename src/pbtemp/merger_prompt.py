"""Interactive questions used to configure a generated project."""

import re as _re
from typing import Any as _Any

import questionary as _questionary
from questionary import Choice as _Choice

from pbtemp.keyvars import BUILD_BACKENDS as _BUILD_BACKENDS
from pbtemp.keyvars import DEFAULTS as _DEFAULTS
from pbtemp.keyvars import OPTION_LABELS as _OPTION_LABELS


def _require_answer(answer: _Any) -> _Any:
    if answer is None:
        raise KeyboardInterrupt
    return answer


def collect_answers() -> dict[str, str | bool | int]:
    """Ask for project metadata, build backend, and optional project features."""
    answers: dict[str, str | bool | int] = {}
    for name in ("project_name", "version", "description"):
        answer = _questionary.text(
            f"{name.replace('_', ' ').capitalize()}: ",
            default=str(_DEFAULTS[name]),
        ).ask()
        answers[name] = str(_require_answer(answer)).strip()

    if not _re.fullmatch(r"[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*", str(answers["project_name"])):
        raise ValueError("Project name must contain only letters, numbers, dots, underscores, and hyphens.")
    if not _re.fullmatch(r"\d+(?:\.\d+)*(?:[a-zA-Z0-9.+-]*)", str(answers["version"])):
        raise ValueError("Version must be a valid numeric version, such as 0.1.0.")

    backend = _questionary.select(
        "Select a build backend:",
        choices=list(_BUILD_BACKENDS),
        default=str(_DEFAULTS["build_backend"]),
    ).ask()
    answers["build_backend"] = str(_require_answer(backend))

    selectable = ("black", "isort", "mypy", "pylint", "pytest", "ruff", "rez_build", "console_script")
    choices = [
        _Choice(
            title=_OPTION_LABELS[name],
            value=name,
            checked=bool(_DEFAULTS[f"use_{name}"]),
        )
        for name in selectable
    ]
    selected = _questionary.checkbox(
        "Select optional tools and features (space to toggle, enter to continue):",
        choices=choices,
    ).ask()
    selected_names = set(_require_answer(selected))
    for name in selectable:
        answers[f"use_{name}"] = name in selected_names

    answers["package_name"] = _re.sub(r"[-.]", "_", str(answers["project_name"])).lower()
    answers["command_name"] = str(answers["project_name"]).replace("_", "-").lower()
    answers["requires_python"] = str(_DEFAULTS["requires_python"])
    answers["line_length"] = int(_DEFAULTS["line_length"])
    return answers
