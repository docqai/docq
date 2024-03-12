"""Slack chat action handler."""

from slack_bolt.context.say import Say

from web.api.integration.slack.slack_application import slack_app
from web.api.integration.utils import chat_completion

CHANNEL_TEMPLATE = "<@{user}> {response}"


@slack_app.event("app_mention")
def handle_app_mention(body: dict, say: Say) -> None:
    """Handle @DocQ App mentions."""
    response = chat_completion(body["event"]["text"])
    say(CHANNEL_TEMPLATE.format(user=body["event"]["user"], response=response), mrkdwn=True)


@slack_app.event("message")
def handle_message_im(body: dict, say: Say) -> None:
    """Handle bot messages."""
    if body["event"]["channel_type"] == "im":
        say(chat_completion(body["event"]["text"]), mrkdwn=True)
