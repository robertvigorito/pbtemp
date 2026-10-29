"""Rez package definition for {{ project_name }}."""

import subprocess

name = "{{ package_name }}"
version = subprocess.check_output(["rezops-get-version"]).decode().strip()
description = "{{ description }}"
requires = []
private_build_requires = []
build_command = f"rezops-build {name}"


def commands() -> bool:
    """Expose the generated package and optional Nuke tools in Rez.

    Returns:
        bool: ``True`` after updating the Rez environment.
    """
    env.PYTHONPATH.append("{root}/python")  # noqa: F821 -- Rez injects ``env`` at runtime.
{% if use_nuke %}    env.NUKE_PATH.append("{root}/src/nuke")  # noqa: F821 -- Rez injects ``env`` at runtime.
{% endif %}
