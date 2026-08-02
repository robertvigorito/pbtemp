"""The module takes the answers and updates the template files with the answers and copies
to the current working directory.
"""

from pathlib import Path as _Path

from jinja2 import Environment as _Environment

# Package imports
from pbtemp.keyvars import get_primary_template_paths as _get_primary_template_paths


def write_templates_to_cwd(answers: dict[str, str], prefix: str = "") -> None:
    """Write the templates to the current working directory with the answers filled in.

    Args:
        answers (dict[str, str]): A dictionary of answers to fill in the templates.
    """

    env = _Environment()
    cwd = _Path.cwd()

    for template in _get_primary_template_paths():
        template_content = template.read_text()
        jinja_template = env.from_string(template_content)
        rendered_content = jinja_template.render(**answers)

        output_file_path = cwd / f"{prefix}{template.name}"
        output_file_path.write_text(rendered_content)
