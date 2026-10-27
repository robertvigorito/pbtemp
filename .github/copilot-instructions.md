# Coding instructions

Apply these guidelines to all project code and tests.

## Style and structure

- Follow PEP 8 with a 120-character configured line length; use Ruff for linting and formatting.
- Before completing Python changes, run `ruff check --fix` and `ruff format` on the changed Python files.
- Use `snake_case` for variables, functions, methods, and modules; `PascalCase` for classes; and `UPPER_CASE` for constants.
- Add type hints to function parameters, return values, and important variables where they clarify intent.
- Keep code simple, readable, focused, and organized into small, single-purpose functions.
- Avoid nested loops and multi-clause comprehensions when they obscure the logic; prefer explicit loops with meaningful intermediate variables unless the concise form is immediately clear.
- Do not define classes inside other classes. Prefer composition over unnecessary inheritance.

## Functions and data

- Prefer keyword arguments when calling functions with multiple arguments.
- Use dataclasses for structured data and `NamedTuple` for lightweight immutable data, rather than passing large unstructured dictionaries when a structured type is appropriate.
- Every function must declare its return type and explicitly return a value. Functions that otherwise would return no data should return `True` or `False` to indicate success or failure. CLI entry points should return an integer exit status (zero for success) when their framework uses the return value as the process exit code. Pytest test functions should return `None` as required by pytest.

## Docstrings

- Use concise Google-style docstrings.
- Add a concise module docstring to every Python module and a class docstring to every class.
- Every function must include a `Returns` section. Include an `Args` section only when the function has parameters; omit it for functions with no arguments. Test functions should document their fixture arguments and `None` return.

## Error handling

- Handle expected errors explicitly and do not silently swallow exceptions.
- Avoid broad `except Exception` unless there is a specific, documented reason.
