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


def collect_answers(
    defaults: dict[str, str | bool | int] | None = None,
) -> dict[str, str | bool | int]:
    """Ask for project details, using supplied values as prompt defaults."""
    prompt_defaults = {**_DEFAULTS, **(defaults or {})}
    answers: dict[str, str | bool | int] = {}
    for name in ("project_name", "version", "description"):
        answer = _questionary.text(
            f"{name.replace('_', ' ').capitalize()}: ",
            default=str(prompt_defaults[name]),
        ).ask()
        answers[name] = str(_require_answer(answer)).strip()

    if not _re.fullmatch(r"[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*", str(answers["project_name"])):
        raise ValueError("Project name must contain only letters, numbers, dots, underscores, and hyphens.")
    if not _re.fullmatch(r"\d+(?:\.\d+)*(?:[a-zA-Z0-9.+-]*)", str(answers["version"])):
        raise ValueError("Version must be a valid numeric version, such as 0.1.0.")

    if prompt_defaults["build_backend"] not in _BUILD_BACKENDS:
        raise ValueError(f"Build backend must be one of: {', '.join(_BUILD_BACKENDS)}.")

    backend = _questionary.select(
        "Select a build backend:",
        choices=list(_BUILD_BACKENDS),
        default=str(prompt_defaults["build_backend"]),
    ).ask()
    answers["build_backend"] = str(_require_answer(backend))

    selectable = ("black", "isort", "mypy", "nuke", "pylint", "pytest", "ruff", "rez_build", "console_script")
    choices = [
        _Choice(
            title=_OPTION_LABELS[name],
            value=name,
            checked=bool(prompt_defaults[f"use_{name}"]),
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
    answers["requires_python"] = str(prompt_defaults["requires_python"])
    answers["line_length"] = int(prompt_defaults["line_length"])
    return answers
