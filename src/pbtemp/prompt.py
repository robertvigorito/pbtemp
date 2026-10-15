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
}


@app.callback()
def cli() -> None:
    """Create a Python project scaffold from the interactive templates."""


@app.command("init")
def init_project(
    output_dir: _Path = _OUTPUT_DIR_OPTION,
) -> None:
    """Interactively create a Python project scaffold."""
    try:
        answers = _collect_answers()
    except KeyboardInterrupt as error:
        raise _typer.Abort() from error
    except ValueError as error:
        raise _typer.BadParameter(str(error)) from error

    written = _write_templates(answers, output_dir=output_dir.expanduser())
    _typer.echo(f"Created {len(written)} project files in {output_dir.expanduser().resolve()}")
    for path in written:
        _typer.echo(f"  {path.relative_to(output_dir.expanduser().resolve())}")


@app.command("test_build")
def test_build() -> None:
    """Generate a fully featured sample scaffold under dist/ without packaging it."""
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
            f"Scaffold copy incomplete: expected {template_count} files, "
            f"found {len(written)}.",
            err=True,
        )
        raise _typer.Exit(code=1)

    _typer.echo(f"Copied all {template_count} template files to {output_dir}.")
    _typer.echo("Complete sample project scaffold created (no wheel built).")


def main() -> None:
    """Run the command-line application."""
    app()
