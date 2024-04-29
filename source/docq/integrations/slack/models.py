"""Slack integration data models."""

from concurrent.futures import thread
from typing import Optional

from attr import dataclass
from sympy import N


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
    thread_ts: Optional[str]
    created_at: str
