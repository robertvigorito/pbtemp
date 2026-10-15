"""Nuke menu setup for {{ project_name }}."""

import nuke  # noqa: I001 -- Nuke provides this host API module.


package_menu = nuke.menu("Nuke").addMenu("{{ project_name }}")
package_menu.addCommand(
    "About",
    lambda: nuke.message("{{ project_name }} Nuke tools"),
)
