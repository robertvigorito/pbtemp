"""Rez package definition for {{ project_name }}."""

name = "{{ package_name }}"
version = "{{ version }}"
description = "{{ description }}"
requires = ["python"]
private_build_requires = []
build_command = "python {root}/rezbuild.py"


def commands():
    """Expose the installed Python package to dependent Rez packages."""
    env.PYTHONPATH.append("{root}/python")
