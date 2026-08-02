"""General code for getting key variables for the package."""

import dataclasses as _dataclasses
import functools as _functools
from pathlib import Path as _Path

import jinja2 as _jinja2
import jinja2.meta as _jinja2_meta

KEY_ASK_ORDER = [
    "project_name",
    "version",
    "description",
]
BUILD_BACKEND_KEY = "build_backend"


def get_primary_template_paths() -> list[_Path]:
    """Get a list of primary template paths in the templates directory.

    Returns:
        list[Path]: A list of Path objects representing the primary template files.
    """
    return list((_Path(__file__).parent.parent / "templates").glob("*"))


def get_filter_nodes(parsed_content: _jinja2.nodes.Template, mapping: dict[str, str]) -> dict[str, str]:
    """Get a mapping of variable names to their default values from the parsed Jinja2 template content.

    Args:
        parsed_content (_jinja2.nodes.Template): The parsed Jinja2 template content.
        mapping (dict[str, str]): A dictionary to store the variable names and their default values.

    Returns:
        dict[str, str]: A dictionary mapping variable names to their default values.
    """
    for node in parsed_content.find_all(_jinja2.nodes.Filter):
        if not isinstance(node.node, _jinja2.nodes.Name):
            continue
        if node.name != "default" or not node.args:
            continue
        default_arg = node.args[0]
        if isinstance(default_arg, _jinja2.nodes.Const):
            mapping[node.node.name] = default_arg.value
    return mapping


def get_filtered_choices(parsed_content: _jinja2.nodes.Template) -> dict[str, list[str]]:
    """Get a mapping of variable names to their possible choices from the parsed Jinja2 template content.

    Args:
        parsed_content (_jinja2.nodes.Template): The parsed Jinja2 template content.

    Returns:
        dict[str, list[str]]: A dictionary mapping variable names to their possible choices.
    """
    choices: dict[str, list[str]] = {}
    for node in parsed_content.find_all(_jinja2.nodes.Compare):
        left = node.expr
        while isinstance(left, _jinja2.nodes.Filter):
            left = left.node
        if not isinstance(left, _jinja2.nodes.Name):
            continue
        for operand in node.ops:
            if operand.op == "eq" and isinstance(operand.expr, _jinja2.nodes.Const):
                choices.setdefault(left.name, []).append(operand.expr.value)
    return choices


@_functools.lru_cache(maxsize=None)
def get_variable_mapping() -> dict[str, str | list[str]]:
    """Search the template for the jinja name and return a mapping of the name to the default value.

    Returns:
        dict[str, str | list[str]]: A dictionary mapping jinja variable names to their default values.
    """
    environment = _jinja2.Environment()
    default_mapping: dict[str, str] = {}

    for template in get_primary_template_paths():
        source = template.read_text()
        parser = environment.parse(source)

        # Capture every variable referenced in the template, defaulting to "".
        for variable in _jinja2_meta.find_undeclared_variables(parser):
            default_mapping.setdefault(variable, "")

        get_filter_nodes(parsed_content=parser, mapping=default_mapping)

        choices = get_filtered_choices(parsed_content=parser)
        if choices and BUILD_BACKEND_KEY in choices:
            default_mapping[BUILD_BACKEND_KEY] = [default_mapping[BUILD_BACKEND_KEY]] + choices[BUILD_BACKEND_KEY]

    return default_mapping


@_dataclasses.dataclass
class SeparatedVariables:
    """A dataclass to hold the separated variables for the package.

    Attributes:
        important (dict[str, str]): A dictionary of important variables and their values.
        build_backend (dict[str, list[str]]): A dictionary of build backend variables and their possible choices.
        use_options (dict[str, str]): A dictionary of other variables and their values.
        others (dict[str, str]): A dictionary of other that dont belong to the above categories.
        original_mapping (dict[str, str]): The original mapping of jinja variable names to their values.
    """

    important: dict[str, str] = _dataclasses.field(default_factory=dict)
    build_backend: dict[str, list[str]] = _dataclasses.field(default_factory=dict)
    use_options: dict[str, str] = _dataclasses.field(default_factory=dict)
    others: dict[str, str] = _dataclasses.field(default_factory=dict)
    original_mapping: dict[str, str] = _dataclasses.field(default_factory=get_variable_mapping)

    @classmethod
    def from_mapping(cls, mapping: dict[str, str] | None = None) -> "SeparatedVariables":
        """Create a SeparatedVariables instance from a mapping.

        Args:
            mapping (dict[str, str] | None): A dictionary mapping jinja variable names to their values.

        Returns:
            SeparatedVariables: An instance of SeparatedVariables with the variables separated into categories.
        """
        cls_instance = cls()
        if mapping is None:
            mapping = cls().original_mapping

        key_ask_order_set = set(KEY_ASK_ORDER)

        for key, value in mapping.items():
            if key in key_ask_order_set:
                cls_instance.important[key] = value
            elif key == BUILD_BACKEND_KEY:
                cls_instance.build_backend[key] = value
            elif key.startswith("use_"):
                cls_instance.use_options[key] = value
            else:
                cls_instance.others[key] = value
        # Sort the important variables based on the order defined in KEY_ASK_ORDER
        cls_instance.important = dict(
            sorted(cls_instance.important.items(), key=lambda item: KEY_ASK_ORDER.index(item[0]))
        )

        return cls_instance

    def get_backend_default(self) -> str | None:
        """Get the default build backend value.

        Returns:
            str | None: The default build backend value, or None if not found.
        """
        return self.build_backend[BUILD_BACKEND_KEY][0]

    def get_backend_choices(self) -> list[str]:
        """Get the list of possible build backend choices.

        Returns:
            list[str]: A list of possible build backend choices.
        """
        return self.build_backend[BUILD_BACKEND_KEY][1:]

    def get_slim_use_names(self) -> list[str]:
        """Get a list of use option names, excluding the important and build backend variables.

        Returns:
            list[str]: A list of use option names.
        """
        return sorted([key.replace("use_", "") for key in self.use_options])

    def get_slim_use_default(self) -> list[str]:
        """Get a list of use option names, excluding the important and build backend variables.

        Returns:
            list[str]: A list of use option names.
        """
        return sorted([key.replace("use_", "") for key, value in self.use_options.items() if value])
