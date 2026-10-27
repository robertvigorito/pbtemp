"""Rez package definition for {{ project_name }}."""

name = "{{ package_name }}"
version = "{{ version }}"
description = "{{ description }}"
requires = ["python"]
private_build_requires = []
build_command = "python {root}/rezbuild.py"


def commands() -> bool:
    """Expose the generated package and optional Nuke tools in Rez.

    Returns:
        bool: ``True`` after updating the Rez environment.
    """
    env.PYTHONPATH.append("{root}/python")  # noqa: F821 -- Rez injects ``env`` at runtime.
{% if use_nuke %}    env.NUKE_PATH.append("{root}/src/nuke")  # noqa: F821 -- Rez injects ``env`` at runtime.
{% endif %}
    return True
