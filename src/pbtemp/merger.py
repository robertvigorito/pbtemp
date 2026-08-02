"""Holder of the merge template for the pbtemp package."""

from dataclasses import dataclass
from pathlib import Path as _Path

from jinja2 import Environment as _Environment
from jinja2 import meta as _meta
from jinja2 import nodes as _nodes
from rich import console as _rich_console
from rich.prompt import Prompt as _Prompt


def get_templates() -> list[_Path]:
    """Get the list of templates for the pbtemp package."""
    return list((_Path(__file__).parent.parent / "templates").glob("*"))


def get_template_keywords(template: _Path) -> set[str]:
    """Get the set of jinja2 keywords/variables used in a template file."""
    env = _Environment()
    source = template.read_text()
    parsed_content = env.parse(source)
    return _meta.find_undeclared_variables(parsed_content)


def get_template_defaults(template: _Path) -> dict[str, str]:
    """Get a mapping of variable -> default value for `{{ var | default(...) }}` usages."""
    env = _Environment()
    source = template.read_text()
    parsed_content = env.parse(source)

    defaults: dict[str, str] = {}
    for node in parsed_content.find_all(_nodes.Filter):
        if node.name == "default" and isinstance(node.node, _nodes.Name) and node.args:
            default_arg = node.args[0]
            if isinstance(default_arg, _nodes.Const):
                defaults[node.node.name] = default_arg.value
    return defaults


console = _rich_console.Console()


# Get the keywords and defaults for jinja2 templates from the templates.

keywords_mapping: dict[str, str] = {}
defaults_mapping: dict[str, str] = {}

for template in get_templates():
    keywords = get_template_keywords(template)
    defaults_mapping.update(get_template_defaults(template))
    for keyword in keywords:
        keywords_mapping.setdefault(keyword, "")


# Ask the user for the values of the keywords in the templates, falling back to defaults.
# for keyword in keywords_mapping:
#     default_value = defaults_mapping.get(keyword, "")
#     prompt = f"Enter value for {keyword}" + (f" [{default_value}]" if default_value else "") + ": "
#     value = console.input(prompt)
#     keywords_mapping[keyword] = value or default_value


# print("\nCollected values for template keywords:")
# for keyword, value in keywords_mapping.items():
#     print(f"{keyword}: {value}")
#     print(f"Default: {defaults_mapping.get(keyword, '')}")
#     print()


# # Take the input values and render the templates to files in the current directory.
# for template in get_templates():
#     env = _Environment()
#     template_content = template.read_text()
#     jinja_template = env.from_string(template_content)
#     rendered_content = jinja_template.render(**keywords_mapping)

#     output_file_path = _Path.cwd() / f"test_{template.name}"
#     output_file_path.write_text(rendered_content)
#     print(f"Rendered {template.name} to {output_file_path}")


def get_template_choices() -> dict[str, set[str]]:
    """Get a mapping of variable -> set of possible values from if/elif == comparisons."""

    template = _Path(__file__).parent.parent / "templates" / "pyproject.toml"
    env = _Environment()
    source = template.read_text()
    parsed_content = env.parse(source)

    choices: dict[str, set[str]] = {}
    for node in parsed_content.find_all(_nodes.Compare):
        # node.expr is the left side, node.ops is a list of Operand(op, expr)
        left = node.expr
        # Unwrap `variable | default(...)` filters to get the underlying Name
        while isinstance(left, _nodes.Filter):
            left = left.node
        if not isinstance(left, _nodes.Name):
            continue
        for operand in node.ops:
            if operand.op == "eq" and isinstance(operand.expr, _nodes.Const):
                choices.setdefault(left.name, set()).add(operand.expr.value)
    return choices


ASK_ORDER = [
    "package_name",
    "version",
    "description",
    "build_backend",
]


print(get_template_choices())


def ask_choice(variable: str, choices: set[str], default: str | None = None) -> str:
    """Prompt the user to pick one value from a set of choices."""
    choice_list = sorted(choices)
    default_value = default if default in choice_list else choice_list[0]
    return _Prompt.ask(
        f"Select [bold]{variable}[/bold]",
        choices=choice_list,
        default=default_value,
    )


import questionary

questionary_prompt = questionary.checkbox(
    "Select build_backend",
    choices=sorted(get_template_choices().get("build_backend", set())),
)
# questionary_answer = questionary_prompt.ask()
