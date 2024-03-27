"""Initialize integrations."""

from .slack import manage_slack


def _init() -> None:
    """Initialize integrations."""
    manage_slack._init()
