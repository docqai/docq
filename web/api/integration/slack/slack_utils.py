"""Slack application utils."""

from docq.integrations.slack import get_slack_bot_token
from slack_sdk import WebClient


def list_slack_team_channels(app_id: str, team_id: str) -> list[dict[str, str]]:
    """List Slack team channels."""
    token = get_slack_bot_token(app_id, team_id)
    client = WebClient(token=token)
    response = client.conversations_list(team_id=team_id, exclude_archived=True, types="public_channel, private_channel")

    return [ channel for channel in response["channels"] if channel["is_member"] ]
