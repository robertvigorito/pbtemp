"""Interactive Python project scaffolding utility."""


def main() -> bool:
    """Run the command-line application.

    Returns:
        bool: ``True`` when the CLI returns normally.
    """
    from pbtemp.prompt import main as run

    run()
    return True


__all__ = ["main"]
