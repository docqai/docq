"""Initialize integrations."""

from .slack import manage_slack, manage_slack_messages


def _init() -> None:
    """Initialize integrations."""
    manage_slack._init()
