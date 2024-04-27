"""Slack chat action handler."""

import logging
from logging import Logger
from typing import Callable

from docq.integrations.slack.slack_application import slack_app
from opentelemetry import trace
from slack_bolt.context.say import Say

from web.api.integration.utils import rag_completion

from .slack_utils import message_handled_middleware, persist_message_middleware

tracer = trace.get_tracer(__name__)

CHANNEL_TEMPLATE = "<@{user}> {response}"

# NOTE: middleware calls inject args so name needs to match. See for all available args https://slack.dev/bolt-python/api-docs/slack_bolt/kwargs_injection/args.html


@slack_app.event("app_mention", middleware=[message_handled_middleware, persist_message_middleware])
@tracer.start_as_current_span(name="handle_app_mention")
def handle_app_mention_event(body: dict, say: Say) -> None:
    """Handle @Docq App mentions."""
    message_replied = False
    if body["event"].get("thead_ts", False):
        # there's a documented bug in the Slack Events API. subtype=message_replied is not being sent. This is the official workaround.
        # https://api.slack.com/events/message/message_replied
        message_replied = True

    ts = body["event"]["ts"]

    # always reply in a thread.
    # if thread_ts is missing it's an unthreaded message so set it as the parent in our response
    thread_ts = body["event"].get("thread_ts", ts)

    print("slack: unthreaded message ", message_replied)

    response = rag_completion(body["event"]["text"], body["event"]["channel"], thread_ts)
    say(
        text=CHANNEL_TEMPLATE.format(user=body["event"]["user"], response=response),
        channel=body["event"]["channel"],
        thread_ts=thread_ts,
        mrkdwn=True,
    )

# TODO: figure out how to save the messages in a thread so we can use it for context.

# @slack_app.event("message", middleware=[message_handled_middleware, persist_message_middleware])
# @tracer.start_as_current_span(name="handle_message")
# def handle_message(body: dict, say: Say) -> None:
#     """Handle bot messages."""
#     logging.debug("Slack message processed.")
# message_replied = False
# if body["event"].get("thead_ts", False):
#     # there's a documented bug in the Slack Events API. subtype=message_replied is not being sent. This is the official workaround.
#     # https://api.slack.com/events/message/message_replied
#     message_replied = True

# print("reply4: unthreaded message ", message_replied)

# response = rag_completion(body["event"]["text"], body["event"]["channel"])
# say(
#     text=CHANNEL_TEMPLATE.format(user=body["event"]["user"], response=response),
#     channel=body["event"]["channel"],
#     thread_ts=body["event"].get("thread_ts", None),
#     mrkdwn=True,
# )
