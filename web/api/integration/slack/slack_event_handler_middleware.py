"""Middleware for Slack event handlers."""
import json
from typing import Callable

import docq.integrations.slack.manage_slack_messages as manage_slack_messages
from opentelemetry import trace
from slack_bolt import Ack

from .slack_event_tracker import SlackEventTracker
from .slack_utils import get_org_id

tracer = trace.get_tracer(__name__)

slack_event_tracker = SlackEventTracker()  # global scope #TODO: move to a function decorator

# NOTE: middleware calls inject args so name needs to match. See for all available args
# @see https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html


@tracer.start_as_current_span(name="filter_duplicate_event_middleware")
def filter_duplicate_event_middleware(ack: Ack, body: dict, next_: Callable) -> None:
    """Middleware to check if an event has already been seen and handled. This prevents duplicate processing of messages.

    Duplicate events are legit. Slack can send the same event multiple times.
    """
    span = trace.get_current_span()

    # print("\033[32mmessage_handled_middleware\033[0m body: ", json.dumps(body, indent=4))

    client_msg_id = body["event"]["client_msg_id"]
    type_ = body["event"]["type"]
    ts = body["event"]["ts"]
    team_id = body["event"]["team"]
    user_id = body["event"]["user"]
    event_id = body.get("event_id")
    thread_ts = body["event"].get("thread_ts")  # None if not a threaded message
    channel_id = body["event"]["channel"]
    org_id = get_org_id(team_id)

    is_duplicate = False
    if event_id:
        is_duplicate = not slack_event_tracker.add_event(event_id=event_id, channel_id=channel_id)

    span.set_attributes(
        attributes={
            "event__client_msg_id": client_msg_id,
            "event__type": type_,
            "event__ts": ts,
            "event__parent_thread_ts": thread_ts or "None",
            "event__team_id": team_id,
            "event__user_id": user_id,
            "event__event_id": str(event_id),
            "event__channel_id": channel_id,
            "event__is_duplicate": is_duplicate,
            "org_id": org_id if org_id else "None",
        }
    )

    if not is_duplicate:
        next_()  # continue processing the event. The main handler will ack
    else:
        ack()  # acknowledge the duplicate event to prevent Slack from resending it


@tracer.start_as_current_span(name="persist_message_middleware")
def persist_message_middleware(body: dict, next_: Callable) -> None:
    """Middleware to persist messages."""
    span = trace.get_current_span()
    print(json.dumps(body, indent=4))
    client_msg_id = body["event"].get("client_msg_id")
    type_ = body["event"]["type"]
    channel = body["event"]["channel"]
    team = body["event"]["team"]
    user = body["event"]["user"]
    text = body["event"]["text"]
    ts = body["event"]["ts"]
    event_id = body.get("event_id")
    thread_ts = str(body["event"].get("thread_ts", None))  # None if not a threaded message
    org_id = get_org_id(team)

    span.set_attributes(
        attributes={
            "event__client_msg_id": client_msg_id or "None",
            "event__type": type_,
            "event__ts": ts,
            "event__parent_thread_ts": thread_ts or "None",
            "event__team_id": team,
            "event__user_id": user,
            "event__event_id": str(event_id),
            "event__channel_id": channel,
            "org_id": org_id or "None",
        }
    )

    if org_id is None:
        span.record_exception(ValueError(f"No Org ID found for Slack team ID '{team}'"))
        span.set_status(trace.StatusCode.ERROR, "No Org ID found")
        raise ValueError(f"No Org ID found for Slack team ID '{team}'")
    manage_slack_messages.insert_or_update_message(
        client_msg_id=client_msg_id,
        type_=type_,
        channel=channel,
        team=team,
        user=user,
        text=text,
        ts=ts,
        thread_ts=thread_ts,
        org_id=org_id,
    )
    next_()
