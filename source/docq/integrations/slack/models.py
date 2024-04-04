"""Slack integration data models."""

from typing import Optional, Self

from attr import dataclass

# class SlackInstallation:
#     """Slack application model."""

#     def __init__(self: Self, data: tuple[str, str, str, int, Optional[int], str]) -> None:
#         """Initialize."""
#         self.app_id = data[0]
#         self.team_id = data[1]
#         self.team_name = data[2]
#         self.org_id = data[3]
#         self.space_group_id = data[4]
#         self.created_at = data[5]

# class SlackChannel:
#     """Slack channel."""

#     def __init__(self: Self, data: tuple[str, str, int, Optional[int], str]) -> None:
#         """Initialize."""
#         self.channel_id = data[0]
#         self.channel_name = data[1]
#         self.org_id = data[2]
#         self.space_group_id = data[3]
#         self.created_at = data[4]


# class SlackMessage:
#     """Slack message."""

#     def __init__(self: Self, data: tuple) -> None:
#         """Initialize."""
#         self.client_msg_id = data[0]
#         self.type = data[1]
#         self.channel = data[2]
#         self.team = data[3]
#         self.user = data[4]
#         self.text = data[5]
#         self.ts = data[6]
#         self.created_at = data[7]


@dataclass
class SlackInstallation:
    """Slack application model."""

    app_id: str
    team_id: str
    team_name: str
    org_id: int
    space_group_id: Optional[int]
    created_at: str


@dataclass
class SlackChannel:
    """Slack channel model."""

    channel_id: str
    channel_name: str
    org_id: int
    space_group_id: Optional[int]
    created_at: str


@dataclass
class SlackMessage:
    """Slack message model."""

    client_msg_id: str
    type: str
    channel_id: str
    team_id: str
    user_id: str
    text: str
    ts: str
    created_at: str
