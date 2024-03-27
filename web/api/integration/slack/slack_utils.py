"""Slack application utils."""

from typing import Callable

import docq.integrations.slack.manage_slack as m_slack
from slack_sdk import WebClient


def list_slack_team_channels(app_id: str, team_id: str) -> list[dict[str, str]]:
    """List Slack team channels."""
    token = m_slack.get_slack_bot_token(app_id, team_id)
    client = WebClient(token=token)
    response = client.conversations_list(team_id=team_id, exclude_archived=True, types="public_channel, private_channel")

    return [ channel for channel in response["channels"] if channel["is_member"] ]


def message_handled_middleware(ack: Callable, body: dict, next_: Callable) -> None:
    """Middleware to check if a message has already been handled. This prevents duplicate processing of messages."""
    ack()

    client_msg_id, ts = body["event"]["client_msg_id"], body["event"]["ts"]
    if m_slack.is_message_handled(client_msg_id, ts):
        return
    next_()

def persist_message_middleware(body: dict, next_: Callable) -> None:
    """Middleware to persist messages."""
    client_msg_id = body["event"]["client_msg_id"]
    type_ = body["event"]["type"]
    channel = body["event"]["channel"]
    team = body["event"]["team"]
    user = body["event"]["user"]
    text = body["event"]["text"]
    ts = body["event"]["ts"]
    m_slack.insert_or_update_message(client_msg_id=client_msg_id, type_=type_, channel=channel, team=team, user=user, text=text, ts=ts )
    next_()
