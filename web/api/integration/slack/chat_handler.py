"""Slack chat action handler."""



from docq.integrations.slack.slack_application import slack_app
from opentelemetry import trace
from slack_bolt.context.say import Say

from web.api.integration.utils import chat_completion, rag_completion

from .slack_utils import message_handled_middleware, persist_message_middleware

tracer = trace.get_tracer(__name__)

CHANNEL_TEMPLATE = "<@{user}> {response}"


@slack_app.event("app_mention", middleware=[message_handled_middleware, persist_message_middleware])
@tracer.start_as_current_span(name="handle_app_mention")
def handle_app_mention(body: dict, say: Say) -> None:
    """Handle @Docq App mentions."""
    response = rag_completion(body["event"]["text"], body["event"]["channel"])
    say(
        text=CHANNEL_TEMPLATE.format(user=body["event"]["user"], response=response),
        channel=body["event"]["channel"],
        mrkdwn=True,
    )

@slack_app.event("message", middleware=[message_handled_middleware, persist_message_middleware])
@tracer.start_as_current_span(name="handle_message_im")
def handle_message_im(body: dict, say: Say) -> None:
    """Handle bot messages."""
    if body["event"]["channel_type"] == "im":
        say(
        text=chat_completion(body["event"]["text"]),
        channel=body["event"]["channel"],
        mrkdwn=True,
    )
