"""Render the selected templates into a destination directory."""

from pathlib import Path as _Path
from typing import Any as _Any

from jinja2 import Environment as _Environment

from pbtemp.keyvars import get_template_paths as _get_template_paths
from pbtemp.keyvars import get_template_root as _get_template_root


def version_up_on_conflict(path: _Path) -> _Path:
    """Return a non-conflicting path by adding a numeric suffix if needed.

    Args:
        path: Candidate output path.

    Returns:
        Path: The original path if available, otherwise a suffixed path.
    """
    if not path.exists():
        return path
    counter = 1
    counter_path = path
    while counter_path.exists():
        counter_path = path.with_name(f"{path.stem}{counter}{path.suffix}")
        counter += 1
    return counter_path


def write_templates_to_cwd(
    answers: dict[str, _Any],
    prefix: str = "",
    output_dir: _Path | str | None = None,
) -> list[_Path]:
    """Render selected templates into the destination directory.

    Existing files are preserved and receive a numeric suffix on collision.

    Args:
        answers: Values used to render the Jinja templates.
        prefix: Optional prefix added to each generated filename.
        output_dir: Destination directory; defaults to the current directory.

    Returns:
        list[Path]: Paths of all files created.
    """
    environment = _Environment(autoescape=False, keep_trailing_newline=True)
    destination = (_Path(output_dir) if output_dir is not None else _Path.cwd()).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    template_root = _get_template_root()
    written: list[_Path] = []

    for template_path in _get_template_paths():
        relative_path = template_path.relative_to(template_root)
        if relative_path.parts[0] == "rez_build" and not answers.get("use_rez_build", False):
            continue
        if relative_path.parts[0] == "tests" and not answers.get("use_pytest", False):
            continue
        if relative_path.parts[0] == "nuke" and not answers.get("use_nuke", False):
            continue
        if relative_path.parts[0] == "docs" and not answers.get("use_mkdocs", False):
            continue
        if relative_path == _Path("mkdocs.yml") and not answers.get("use_mkdocs", False):
            continue
        if relative_path.parts[0] == "package":
            relative_path = _Path("src", answers["package_name"], *relative_path.parts[1:])
        if prefix:
            relative_path = relative_path.with_name(f"{prefix}{relative_path.name}")

        output_path = destination / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path = version_up_on_conflict(output_path)
        rendered = environment.from_string(template_path.read_text(encoding="utf-8")).render(**answers)
        output_path.write_text(rendered, encoding="utf-8")
        written.append(output_path)

    return written
