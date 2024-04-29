"""Slack event handlers aka listeners."""

from docq.integrations.slack.slack_application import slack_app
from opentelemetry import trace
from slack_bolt import Ack
from slack_bolt.context.say import Say

from web.api.integration.utils import rag_completion

from .slack_event_handler_middleware import (
    filter_duplicate_event_middleware,
    persist_message_middleware,
)

tracer = trace.get_tracer(__name__)


CHANNEL_TEMPLATE = "<@{user}> {response}"

# NOTE: middleware calls inject args so name needs to match. See for all available args https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html


@slack_app.event("app_mention", middleware=[filter_duplicate_event_middleware])
@tracer.start_as_current_span(name="handle_app_mention")
def handle_app_mention_event(body: dict, ack: Ack, say: Say) -> None:
    """Handle of type app_mention. i.e. [at]botname."""
    span = trace.get_current_span()
    is_thread_message = False
    if body["event"].get("thread_ts", False):
        # there's a documented bug in the Slack Events API. subtype=message_replied is not being sent. This is the official workaround.
        # https://api.slack.com/events/message/message_replied
        is_thread_message = True

    ts = body["event"]["ts"]
    # always reply in a thread.
    # if thread_ts is missing it's an unthreaded message so set it as the parent in our response
    thread_ts = body["event"].get("thread_ts", ts)
    text = body["event"]["text"]
    event_id = body.get("event_id")
    channel_id = body["event"]["channel"]
    user_id = body["event"]["user"]

    try:
        ack()
        response = rag_completion(text=text, channel_id=channel_id, thread_ts=thread_ts)
        say(
            text=CHANNEL_TEMPLATE.format(user=user_id, response=response),
            channel=channel_id,
            thread_ts=thread_ts,
            mrkdwn=True,
        )
    except Exception as e:
        span.record_exception(e)
        span.set_status(trace.StatusCode.ERROR, str(e))
        raise e


@slack_app.event("message", middleware=[persist_message_middleware])
@tracer.start_as_current_span(name="handle_message")
def handle_message(body: dict, ack: Ack, say: Say) -> None:
    """Events of type message. This fires for multiple types including app_mention."""
    Ack()
