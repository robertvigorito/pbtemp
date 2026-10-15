"""Command-line interface for creating Python project scaffolds."""

from pathlib import Path as _Path

import typer as _typer

from pbtemp.combine import write_templates_to_cwd as _write_templates
from pbtemp.keyvars import DEFAULTS as _DEFAULTS
from pbtemp.keyvars import get_template_paths as _get_template_paths
from pbtemp.merger_prompt import collect_answers as _collect_answers

app = _typer.Typer(
    no_args_is_help=True,
    help="Create a new Python package structure from the bundled templates.",
)
_OUTPUT_DIR_OPTION = _typer.Option(
    _Path.cwd(),
    "--output-dir",
    "-o",
    file_okay=False,
    dir_okay=True,
    help="Directory in which to create the project files (defaults to the current directory).",
)
_TEST_BUILD_ANSWERS: dict[str, str | bool | int] = {
    **_DEFAULTS,
    "project_name": "pbtemp-test-build",
    "package_name": "pbtemp_test_build",
    "command_name": "pbtemp-test-build",
    "version": "0.1.0",
    "description": "Sample project used to verify scaffold generation.",
    "build_backend": "uv_build",
    "use_console_script": True,
    "use_black": True,
    "use_isort": True,
    "use_mypy": True,
    "use_pylint": True,
    "use_pytest": True,
    "use_ruff": True,
    "use_rez_build": True,
    "use_nuke": True,
}


@app.callback()
def cli() -> bool:
    """Initialize the scaffold CLI.

    Returns:
        bool: ``True`` when command dispatch can proceed.
    """
    return True


@app.command("init")
def init_project(
    output_dir: _Path = _OUTPUT_DIR_OPTION,
    project_name: str | None = _typer.Option(
        None,
        "--project-name",
        help="Default project name shown in the interactive prompt.",
    ),
    version: str | None = _typer.Option(
        None,
        "--version",
        help="Default version shown in the interactive prompt.",
    ),
    description: str | None = _typer.Option(
        None,
        "--description",
        help="Default description shown in the interactive prompt.",
    ),
    build_backend: str | None = _typer.Option(
        None,
        "--build-backend",
        help="Default build backend selection.",
    ),
    requires_python: str | None = _typer.Option(
        None,
        "--requires-python",
        help="Default Python version requirement.",
    ),
    line_length: int | None = _typer.Option(
        None,
        "--line-length",
        min=1,
        help="Default configured line length.",
    ),
    use_console_script: bool | None = _typer.Option(
        None,
        "--use-console-script/--no-use-console-script",
        help="Default whether to add a console script.",
    ),
    use_black: bool | None = _typer.Option(
        None,
        "--use-black/--no-use-black",
        help="Default whether to include Black.",
    ),
    use_isort: bool | None = _typer.Option(
        None,
        "--use-isort/--no-use-isort",
        help="Default whether to include isort.",
    ),
    use_mypy: bool | None = _typer.Option(
        None,
        "--use-mypy/--no-use-mypy",
        help="Default whether to include mypy.",
    ),
    use_nuke: bool | None = _typer.Option(
        None,
        "--use-nuke/--no-use-nuke",
        help="Default whether to include Nuke startup and menu files.",
    ),
    use_pylint: bool | None = _typer.Option(
        None,
        "--use-pylint/--no-use-pylint",
        help="Default whether to include Pylint.",
    ),
    use_pytest: bool | None = _typer.Option(
        None,
        "--use-pytest/--no-use-pytest",
        help="Default whether to include pytest.",
    ),
    use_ruff: bool | None = _typer.Option(
        None,
        "--use-ruff/--no-use-ruff",
        help="Default whether to include Ruff.",
    ),
    use_rez_build: bool | None = _typer.Option(
        None,
        "--use-rez-build/--no-use-rez-build",
        help="Default whether to include Rez build support.",
    ),
) -> bool:
    """Interactively create a Python project scaffold.

    Args:
        output_dir: Destination directory for generated files.
        project_name: Default project name for the prompt.
        version: Default project version for the prompt.
        description: Default project description for the prompt.
        build_backend: Default build backend selection.
        requires_python: Default supported Python version specifier.
        line_length: Default configured source line length.
        use_console_script: Default console entry-point selection.
        use_black: Default Black selection.
        use_isort: Default isort selection.
        use_mypy: Default mypy selection.
        use_nuke: Default Nuke support selection.
        use_pylint: Default Pylint selection.
        use_pytest: Default pytest selection.
        use_ruff: Default Ruff selection.
        use_rez_build: Default Rez support selection.

    Returns:
        bool: ``True`` after all generated files are reported.

    Raises:
        typer.Abort: If an interactive prompt is cancelled.
        typer.BadParameter: If supplied defaults are invalid.
    """
    defaults = {
        name: value
        for name, value in {
            "project_name": project_name,
            "version": version,
            "description": description,
            "build_backend": build_backend,
            "requires_python": requires_python,
            "line_length": line_length,
            "use_console_script": use_console_script,
            "use_black": use_black,
            "use_isort": use_isort,
            "use_mypy": use_mypy,
            "use_nuke": use_nuke,
            "use_pylint": use_pylint,
            "use_pytest": use_pytest,
            "use_ruff": use_ruff,
            "use_rez_build": use_rez_build,
        }.items()
        if value is not None
    }
    try:
        answers = _collect_answers(defaults=defaults)
    except KeyboardInterrupt as error:
        raise _typer.Abort() from error
    except ValueError as error:
        raise _typer.BadParameter(str(error)) from error

    written = _write_templates(answers, output_dir=output_dir.expanduser())
    _typer.echo(f"Created {len(written)} project files in {output_dir.expanduser().resolve()}")
    for path in written:
        _typer.echo(f"  {path.relative_to(output_dir.expanduser().resolve())}")
    return True


@app.command("build-temp")
def build_temp() -> bool:
    """Generate a fully featured sample scaffold under dist/.

    Returns:
        bool: ``True`` when all template files are written.

    Raises:
        typer.Exit: If not all bundled templates can be copied.
    """
    template_count = len(_get_template_paths())
    distribution_dir = _Path.cwd() / "dist"
    distribution_dir.mkdir(parents=True, exist_ok=True)
    output_dir = distribution_dir / str(_TEST_BUILD_ANSWERS["project_name"])
    suffix = 1
    while output_dir.exists():
        output_dir = distribution_dir / f"{_TEST_BUILD_ANSWERS['project_name']}-{suffix}"
        suffix += 1

    written = _write_templates(_TEST_BUILD_ANSWERS, output_dir=output_dir)
    if len(written) != template_count or any(not path.is_file() for path in written):
        _typer.echo(
            f"Scaffold copy incomplete: expected {template_count} files, found {len(written)}.",
            err=True,
        )
        raise _typer.Exit(code=1)

    _typer.echo(f"Copied all {template_count} template files to {output_dir}.")
    _typer.echo("Complete sample project scaffold created (no wheel built).")
    return True


def main() -> bool:
    """Run the Typer command-line application.

    Returns:
        bool: ``True`` when the CLI returns normally.
    """
    app()
    return True
