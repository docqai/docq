"""Slack installation modles."""

from typing import Self


class SlackInstallation:
    """Slack application."""

    def __init__(self: Self, data: tuple[str, str, str, int, int, str]) -> None:
        """Initialize."""
        self.app_id = data[0]
        self.team_id = data[1]
        self.team_name = data[2]
        self.org_id = data[3]
        self.space_group_id = data[4]
        self.created_at = data[5]

class SlackChannel:
    """Slack channel."""

    def __init__(self: Self, data: tuple[str, str, int, int, str]) -> None:
        """Initialize."""
        self.channel_id = data[0]
        self.channel_name = data[1]
        self.org_id = data[2]
        self.space_group_id = data[3]
        self.created_at = data[4]

