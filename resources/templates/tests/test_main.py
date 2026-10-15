"""Starter test module for the generated package."""

from typing import Any

from {{ package_name }}.main import main


def test_main_prints_greeting(capsys: Any) -> None:
    """Check that the example entry point prints its greeting.

    Args:
        capsys: Pytest fixture that captures standard output.

    Returns:
        None: Assertions validate the captured greeting.
    """
    assert main() == 0
    assert capsys.readouterr().out == "Hello from {{ project_name }}!\n"
    return None
