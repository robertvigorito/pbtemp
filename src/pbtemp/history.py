"""Persistent storage for the user's most recently selected scaffold options."""

import json as _json
import os as _os
from pathlib import Path as _Path
from tempfile import NamedTemporaryFile as _NamedTemporaryFile
from typing import Any as _Any

from platformdirs import user_config_path as _user_config_path

from pbtemp.keyvars import DEFAULTS as _DEFAULTS

HISTORY_PATH = _user_config_path("pbtemp", "pbtemp") / "history.json"
_HISTORY_VERSION = 1
_HISTORY_OPTIONS = frozenset(
    {
        *_DEFAULTS,
        "package_name",
        "command_name",
    }
)


def read_history() -> dict[str, str | bool | int]:
    """Read the last saved prompt answers, or return an empty mapping.

    Returns:
        dict[str, str | bool | int]: Valid remembered prompt options.

    Raises:
        ValueError: If the history file exists but is invalid or unsupported.
        OSError: If the history file cannot be read.
    """
    if not HISTORY_PATH.exists():
        return {}

    try:
        document = _json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except _json.JSONDecodeError as error:
        raise ValueError(f"History file is not valid JSON: {HISTORY_PATH}") from error
    if not validate_history_document(document):
        raise ValueError(f"History file has an unsupported format: {HISTORY_PATH}")

    options = document["options"]
    valid_options: dict[str, str | bool | int] = {}
    for key, value in options.items():
        if key in _HISTORY_OPTIONS and isinstance(value, (str, bool, int)):
            valid_options[key] = value
    return valid_options


def write_history(options: dict[str, str | bool | int]) -> bool:
    """Atomically save known prompt answers for the next scaffold run.

    Args:
        options: Prompt answers to remember.

    Returns:
        bool: ``True`` after the history file has been saved.

    Raises:
        OSError: If the history file cannot be written.
    """
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    safe_options = {
        key: value for key, value in options.items() if key in _HISTORY_OPTIONS and isinstance(value, (str, bool, int))
    }
    payload = _json.dumps(
        {"version": _HISTORY_VERSION, "options": safe_options},
        indent=2,
        sort_keys=True,
    )
    temporary_path: _Path | None = None
    try:
        with _NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=HISTORY_PATH.parent,
            prefix=f".{HISTORY_PATH.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = _Path(temporary_file.name)
            temporary_file.write(f"{payload}\n")
        _os.replace(temporary_path, HISTORY_PATH)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    return True


def serialize_history(options: dict[str, str | bool | int]) -> str:
    """Format remembered options as readable JSON for display and export.

    Args:
        options: Prompt options to format.

    Returns:
        str: Indented JSON representation of the options.
    """
    return _json.dumps(options, indent=2, sort_keys=True)


def validate_history_document(document: _Any) -> bool:
    """Validate the outer history document shape.

    Args:
        document: Decoded JSON value.

    Returns:
        bool: ``True`` when the document uses the supported schema.
    """
    return (
        isinstance(document, dict)
        and document.get("version") == _HISTORY_VERSION
        and isinstance(document.get("options"), dict)
    )
