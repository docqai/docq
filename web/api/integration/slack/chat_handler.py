"""Slack chat action handler."""

from typing import Callable

from slack_bolt.context.say import Say

from web.api.integration.slack.slack_application import slack_app
from web.api.integration.utils import chat_completion, rag_completion

CHANNEL_TEMPLATE = "<@{user}> {response}"


@slack_app.event("app_mention")
def handle_app_mention(ack: Callable, body: dict, say: Say) -> None:
    """Handle @DocQ App mentions."""
    ack()
    response = rag_completion(body["event"]["text"], body["event"]["channel"])
    say(
        text=CHANNEL_TEMPLATE.format(user=body["event"]["user"], response=response),
        channel=body["event"]["channel"],
        mrkdwn=True,
    )


@slack_app.event("message")
def handle_message_im(ack: Callable, body: dict, say: Say) -> None:
    """Handle bot messages."""
    ack()
    if body["event"]["channel_type"] == "im":
        say(
        text=chat_completion(body["event"]["text"]),
        channel=body["event"]["channel"],
        mrkdwn=True,
    )
