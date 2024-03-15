"""DocQ bot app home."""

from typing import Any

from web.api.integration.slack.slack_application import slack_app


@slack_app.event("app_installed")
def app_installed(event: Any, logger: Any) -> None:
    """App installed event."""
    logger.info(event)


@slack_app.event("app_home_opened")
def handle_app_home_opened_events(client: Any, event: Any, logger: Any) -> None:
    """Handle app home opened events."""
    client.views_publish(
        user_id=event["user"],
        view={
            "type": "home",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hello :wave: <@{event['user']}> Welcome to DocQ!.\n\n",
                    },
                },
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "Docq.AI Your private ChatGPT alternative", "emoji": True},
                },
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "plain_text",
                            "text": "Securely unlock knowledge from your business documents. Give your employees' a second-brain.",
                            "emoji": True,
                        }
                    ],
                },
                {
                    "type": "image",
                    "image_url": "https://camo.githubusercontent.com/dc0e67c1884b3629ad73259f7f32ffcadcf974b4c92a1ebb9eaa2ffd0cfb2825/68747470733a2f2f646f637161692e6769746875622e696f2f646f63712f6173736574732f646f63712d646961672d6e6f76323032332e706e67",
                    "alt_text": "Docq overview",
                },
            ],
        },
    )
