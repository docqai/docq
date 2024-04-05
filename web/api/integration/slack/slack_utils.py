"""Slack application utils."""

from typing import Callable

import docq.integrations.slack.manage_slack as manage_slack
import docq.integrations.slack.manage_slack_messages as manage_slack_messages
import streamlit as st
from opentelemetry import trace
from slack_sdk import WebClient

tracer = trace.get_tracer(__name__)


@st.cache_data(ttl=6000)
def get_org_id(team_id: str) -> int | None:
    """Get the org id for a Slack team / workspace."""
    result = manage_slack.list_docq_slack_installations(org_id=None, team_id=team_id)
    return result[0].org_id if result else None


@tracer.start_as_current_span(name="list_slack_team_channels")
def list_slack_team_channels(app_id: str, team_id: str) -> list[dict[str, str]]:
    """List Slack team channels."""
    token = manage_slack.get_slack_bot_token(app_id, team_id)
    client = WebClient(token=token)
    response = client.conversations_list(team_id=team_id, exclude_archived=True, types="public_channel, private_channel")

    return [ channel for channel in response["channels"] if channel["is_member"] ]

@tracer.start_as_current_span(name="get_slack_channel")
def message_handled_middleware(ack: Callable, body: dict, next_: Callable) -> None:
    """Middleware to check if a message has already been handled. This prevents duplicate processing of messages."""
    span = trace.get_current_span()
    ack()

    client_msg_id, ts, team_id = body["event"]["client_msg_id"], body["event"]["ts"], body["event"]["team"]
    org_id = get_org_id(team_id)
    if org_id is None:
        span.record_exception(ValueError(f"No Org ID found for Slack team ID '{team_id}'"))
        span.set_status(trace.StatusCode.ERROR, "No Org ID found")
        raise ValueError(f"No Org ID found for Slack team ID '{team_id}'")
    if manage_slack_messages.is_message_handled(client_msg_id, ts, org_id):
        return
    next_()

@tracer.start_as_current_span(name="persist_message_middleware")
def persist_message_middleware(body: dict, next_: Callable) -> None:
    """Middleware to persist messages."""
    span = trace.get_current_span()
    client_msg_id = body["event"]["client_msg_id"]
    type_ = body["event"]["type"]
    channel = body["event"]["channel"]
    team = body["event"]["team"]
    user = body["event"]["user"]
    text = body["event"]["text"]
    ts = body["event"]["ts"]
    org_id = get_org_id(team)
    if org_id is None:
        span.record_exception(ValueError(f"No Org ID found for Slack team ID '{team}'"))
        span.set_status(trace.StatusCode.ERROR, "No Org ID found")
        raise ValueError(f"No Org ID found for Slack team ID '{team}'")
    manage_slack_messages.insert_or_update_message(
        client_msg_id=client_msg_id, type_=type_, channel=channel, team=team, user=user, text=text, ts=ts, org_id=org_id
    )
    next_()
