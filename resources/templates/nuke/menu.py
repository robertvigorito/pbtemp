"""Nuke menu setup for {{ project_name }}."""

import nuke


package_menu = nuke.menu("Nuke").addMenu("{{ project_name }}")
package_menu.addCommand(
    "About",
    lambda: nuke.message("{{ project_name }} Nuke tools"),
)
