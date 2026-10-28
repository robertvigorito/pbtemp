"""Command-line interface for creating Python project scaffolds."""

from pathlib import Path as _Path

import typer as _typer

from pbtemp.combine import get_template_operations as _get_template_operations
from pbtemp.combine import write_templates_to_cwd as _write_templates
from pbtemp.history import read_history as _read_history
from pbtemp.history import serialize_history as _serialize_history
from pbtemp.history import write_history as _write_history
from pbtemp.keyvars import DEFAULTS as _DEFAULTS
from pbtemp.keyvars import get_template_paths as _get_template_paths
from pbtemp.merge import SUPPORTED_MERGE_OPERATIONS as _SUPPORTED_MERGE_OPERATIONS
from pbtemp.merge import get_existing_project_defaults as _get_existing_project_defaults
from pbtemp.merge import merge_project_templates as _merge_project_templates
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


def _complete_merge_operation(ctx: _typer.Context, incomplete: str) -> list[str]:
    """Suggest configured merge operations matching the current input.

    Args:
        ctx: Typer context containing parsed merge options.
        incomplete: Partial operation value typed by the user.

    Returns:
        list[str]: Matching configured operation names.
    """
    output_dir = ctx.params.get("output_dir", _Path.cwd())
    project_dir = _Path(output_dir).expanduser().resolve()
    try:
        operations = _get_template_operations(project_dir)
    except (OSError, ValueError):
        return []
    return [name for name in operations if name.startswith(incomplete.lower())]


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
    "use_mkdocs": True,
    "use_mypy": True,
    "use_pylint": True,
    "use_pytest": True,
    "use_pytest_sugar": True,
    "use_coverage": True,
    "use_ruff": True,
    "use_rez_build": True,
    "use_nuke": True,
}
history_app = _typer.Typer(no_args_is_help=True, help="Read and edit remembered prompt options.")
app.add_typer(history_app, name="history")


def _load_history_defaults(ignore_history: bool) -> dict[str, str | bool | int]:
    """Load remembered values unless history use was disabled for this run.

    Args:
        ignore_history: Whether to skip loading the saved prompt answers.

    Returns:
        dict[str, str | bool | int]: Remembered defaults, or an empty mapping.
    """
    if ignore_history:
        return {}
    try:
        return _read_history()
    except (OSError, ValueError) as error:
        _typer.echo(f"Warning: could not read saved history: {error}", err=True)
        return {}


def _save_history(answers: dict[str, str | bool | int]) -> bool:
    """Save successful prompt answers, warning rather than failing generation.

    Args:
        answers: Prompt answers from a completed generation or merge.

    Returns:
        bool: ``True`` if history was saved successfully.
    """
    try:
        _write_history(answers)
    except OSError as error:
        _typer.echo(f"Warning: could not save prompt history: {error}", err=True)
        return False
    return True


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
    use_mkdocs: bool | None = _typer.Option(
        None,
        "--use-mkdocs/--no-use-mkdocs",
        help="Default whether to include MkDocs documentation files and tooling.",
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
    use_pytest_sugar: bool | None = _typer.Option(
        None,
        "--use-pytest-sugar/--no-use-pytest-sugar",
        help="Default whether to include pytest-sugar output formatting.",
    ),
    use_coverage: bool | None = _typer.Option(
        None,
        "--use-coverage/--no-use-coverage",
        help="Default whether to include pytest-cov and enable coverage reporting.",
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
    ignore_history: bool = _typer.Option(
        False,
        "--ignore-history",
        "--no-history",
        help=("Do not use previously saved answers for this run (answers are still saved afterward)."),
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
        use_mkdocs: Default MkDocs documentation selection.
        use_nuke: Default Nuke support selection.
        use_pylint: Default Pylint selection.
        use_pytest: Default pytest selection.
        use_pytest_sugar: Default pytest-sugar selection.
        use_coverage: Default coverage reporting selection.
        use_ruff: Default Ruff selection.
        use_rez_build: Default Rez support selection.
        ignore_history: Whether to skip remembered prompt values for this run.

    Returns:
        bool: ``True`` after all generated files are reported.

    Raises:
        typer.Abort: If an interactive prompt is cancelled.
        typer.BadParameter: If supplied defaults are invalid.
    """
    explicit_defaults = {
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
            "use_mkdocs": use_mkdocs,
            "use_mypy": use_mypy,
            "use_nuke": use_nuke,
            "use_pylint": use_pylint,
            "use_pytest": use_pytest,
            "use_pytest_sugar": use_pytest_sugar,
            "use_coverage": use_coverage,
            "use_ruff": use_ruff,
            "use_rez_build": use_rez_build,
        }.items()
        if value is not None
    }
    defaults = {**_load_history_defaults(ignore_history), **explicit_defaults}
    try:
        answers = _collect_answers(defaults=defaults)
    except KeyboardInterrupt as error:
        raise _typer.Abort() from error
    except ValueError as error:
        raise _typer.BadParameter(str(error)) from error

    project_name = str(answers["project_name"])
    answers["package_name"] = project_name.replace("-", "_").replace(".", "_").lower()
    answers["command_name"] = project_name.replace("_", "-").lower()
    written = _write_templates(answers, output_dir=output_dir.expanduser())
    _save_history(answers)
    _typer.echo(f"Created {len(written)} project files in {output_dir.expanduser().resolve()}")
    for path in written:
        _typer.echo(f"  {path.relative_to(output_dir.expanduser().resolve())}")
    return True


@app.command("merge")
def merge_project(
    output_dir: _Path = _OUTPUT_DIR_OPTION,
    operation: list[str] = _typer.Option(
        ["all"],
        "--operation",
        "-m",
        case_sensitive=False,
        autocompletion=_complete_merge_operation,
        help=(
            "Select one or more template groups; repeat --operation. Available: "
            + ", ".join(_SUPPORTED_MERGE_OPERATIONS)
            + "."
        ),
    ),
    hard_replace: bool = _typer.Option(
        False,
        "--hard-replace",
        "--replace-makefile",
        "--replace",
        help="Replace existing generated files in selected operation scopes instead of merging or preserving them.",
    ),
    ignore_history: bool = _typer.Option(
        False,
        "--ignore-history",
        "--no-history",
        help=("Do not use previously saved answers for this run (answers are still saved afterward)."),
    ),
) -> bool:
    """Merge current templates into an existing Python project.

    Existing pyproject settings are preserved while missing template configuration
    and dependencies are added. Existing files are preserved by default; the
    --replace option overwrites generated files selected by the operation scopes.

    Args:
        output_dir: Root directory of the existing project.
        operation: One or more template migration scopes to apply.
        hard_replace: Whether to replace existing generated files in the selected scopes.
        ignore_history: Whether to skip remembered prompt values for this run.

    Returns:
        bool: ``True`` after the project has been merged.

    Raises:
        typer.Abort: If the interactive feature prompt is cancelled.
        typer.BadParameter: If the directory lacks valid Python project metadata.
    """
    project_dir = output_dir.expanduser().resolve()
    operation_names = [name.lower() for name in operation]
    try:
        supported_operations = tuple(_get_template_operations(project_dir))
        unknown_operations = sorted(set(operation_names) - set(supported_operations))
        if unknown_operations:
            raise _typer.BadParameter(
                f"Invalid operation(s) {', '.join(repr(name) for name in unknown_operations)}. "
                f"Choose from: {', '.join(supported_operations)}."
            )
        defaults = {
            **_load_history_defaults(ignore_history),
            **_get_existing_project_defaults(project_dir, include_fallbacks=False),
        }
        answers = _collect_answers(defaults=defaults)
        changed = _merge_project_templates(
            answers=answers,
            project_dir=project_dir,
            operation=operation_names,
            hard_replace=hard_replace,
        )
    except KeyboardInterrupt as error:
        raise _typer.Abort() from error
    except (FileNotFoundError, ValueError) as error:
        raise _typer.BadParameter(str(error)) from error

    _save_history(answers)
    _typer.echo(f"Merged template configuration and added {len(changed)} files in {project_dir}.")
    for path in changed:
        _typer.echo(f"  {path.relative_to(project_dir)}")
    return True


def _display_history() -> bool:
    """Print remembered options as JSON.

    Returns:
        bool: ``True`` when the history was displayed.
    """
    try:
        options = _read_history()
    except (OSError, ValueError) as error:
        raise _typer.BadParameter(str(error)) from error
    if not options:
        _typer.echo("No saved prompt history.")
    else:
        _typer.echo(_serialize_history(options))
    return True


@history_app.command("dump")
def dump_history() -> bool:
    """Dump remembered prompt options as JSON.

    Returns:
        bool: ``True`` when the history was displayed.
    """
    return _display_history()


@history_app.command("show")
def show_history() -> bool:
    """Read remembered prompt options.

    Returns:
        bool: ``True`` when the history was displayed.
    """
    return _display_history()


@history_app.command("edit")
def edit_history() -> bool:
    """Interactively edit and save remembered prompt options.

    Returns:
        bool: ``True`` when the edited history was saved.

    Raises:
        typer.Abort: If an interactive prompt is cancelled.
        typer.BadParameter: If saved history is invalid.
    """
    defaults = _load_history_defaults(ignore_history=False)
    try:
        answers = _collect_answers(defaults=defaults)
    except KeyboardInterrupt as error:
        raise _typer.Abort() from error
    except ValueError as error:
        raise _typer.BadParameter(str(error)) from error
    if _save_history(answers):
        _typer.echo("Saved prompt history.")
    return True


@app.command("build-temp")
def build_temp() -> bool:
    """Generate a fully featured sample scaffold under dist/.

    Returns:
        bool: ``True`` when all template files are written.

    Raises:
        typer.Exit: If not all bundled templates can be copied.
    """
    # ``write_templates_to_cwd`` also emits a project-local pbtemp.toml path-map.
    template_count = len(_get_template_paths()) + 1
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
