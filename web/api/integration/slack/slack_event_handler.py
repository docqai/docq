"""Slack chat action handler."""

from docq.integrations.slack.slack_application import slack_app
from opentelemetry import trace
from slack_bolt.context.say import Say

from web.api.integration.utils import rag_completion

from .slack_event_handler_middleware import (
    filter_duplicate_event_middleware,
    persist_message_middleware,
    slack_event_tracker,
)

tracer = trace.get_tracer(__name__)


CHANNEL_TEMPLATE = "<@{user}> {response}"

# NOTE: middleware calls inject args so name needs to match. See for all available args https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html


@slack_app.event("app_mention", middleware=[filter_duplicate_event_middleware])
@tracer.start_as_current_span(name="handle_app_mention")
def handle_app_mention_event(body: dict, say: Say) -> None:
    """Handle of type app_mention. i.e. [at]botname."""
    is_thread_message = False
    if body["event"].get("thread_ts", False):
        # there's a documented bug in the Slack Events API. subtype=message_replied is not being sent. This is the official workaround.
        # https://api.slack.com/events/message/message_replied
        is_thread_message = True

    ts = body["event"]["ts"]
    # always reply in a thread.
    # if thread_ts is missing it's an unthreaded message so set it as the parent in our response
    thread_ts = body["event"].get("thread_ts", ts)
    event_id = body.get("event_id")
    channel_id = body["event"]["channel"]

    print("slack: unthreaded message ", is_thread_message)

    response = rag_completion(body["event"]["text"], body["event"]["channel"], thread_ts)
    say(
        text=CHANNEL_TEMPLATE.format(user=body["event"]["user"], response=response),
        channel=body["event"]["channel"],
        thread_ts=thread_ts,
        mrkdwn=True,
    )
    # if event_id:
    #     slack_event_tracker.remove_event(event_id=event_id, channel_id=channel_id)


@slack_app.event("message", middleware=[persist_message_middleware])
@tracer.start_as_current_span(name="handle_message")
def handle_message(body: dict, say: Say) -> None:
    """Events of type message. This fires for multiple types including app_mention."""
