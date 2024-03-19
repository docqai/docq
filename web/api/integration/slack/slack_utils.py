"""Slack application utils."""

from web.api.integration.slack.slack_application import slack_app


def list_slack_team_channels(team_id: str) -> list[dict[str, str]]:
    """List Slack team channels."""
    client = slack_app.client
    response = client.conversations_list(team_id=team_id, exclude_archived=True, types="public_channel, private_channel")

    return [ channel for channel in response["channels"] if channel["is_member"] ]
