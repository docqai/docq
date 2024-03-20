"""Initialize integrations."""

from . import manage_slack


def _init() -> None:
    """Initialize integrations."""
    manage_slack._init()
