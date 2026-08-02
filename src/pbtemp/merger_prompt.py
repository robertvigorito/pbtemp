"""Module for handling merger prompts."""

from pbtemp import keyvars as _keyvars
import rich.console as _rich_console
import rich.pretty as _rich_pretty
import questionary as _questionary


# Ask the important questions first, then the build backend, then the rest of the use options.

separated_variables = _keyvars.SeparatedVariables.from_mapping()
mapping = {}

for important_name, default_value in separated_variables.important.items():
    question = _questionary.text(
        message=f"Enter value for {important_name.replace('_', ' ')}:  ",
        default=default_value,
    ).ask()
    if question:
        mapping[important_name] = question

question = _questionary.select(
    message="Select a build backend:  ",
    choices=separated_variables.get_backend_choices(),
    default=separated_variables.get_backend_default(),
).ask()
if question:
    mapping[_keyvars.BUILD_BACKEND_KEY] = question

choices = [
    _questionary.Choice(title=name, checked=(name in separated_variables.get_slim_use_default()))
    for name in separated_variables.get_slim_use_names()
]
question_for_use = _questionary.checkbox(
    message="Select use options:  ",
    choices=choices,
).ask()

for answer in question_for_use:
    mapping[f"use_{answer}"] = "true"


# Use rich to print out the dictionary of variables and their values in a pretty way.
console = _rich_console.Console()
console.print("Collected values for template keywords:", style="bold cyan")
console.print(_rich_pretty.Pretty(mapping, expand_all=True))

from pbtemp.combine import write_templates_to_cwd as _write_templates_to_cwd

_write_templates_to_cwd(mapping, "testing")
