"""DocQ bot app home."""

from typing import Any, Callable

import docq.integrations.slack.slack_application as slack
from slack_sdk import WebClient


def get_header_block() -> dict[str, Any]:
    """Get header block."""
    return {
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": "Docq.AI Your private ChatGPT alternative",
            "emoji": True
        }
    }

def get_divider_block() -> dict[str, Any]:
    """Get divider block."""
    return { "type": "divider" }

def get_context_block() -> dict[str, Any]:
    """Get context block."""
    return {
        "type": "context",
        "elements": [
            {
                "type": "plain_text",
                "text": "Securely unlock knowledge from your business documents. Give your employees' a second-brain.",
                "emoji": True
            }
        ]
    }

def get_image_block() -> dict[str, Any]:
    """Get image block."""
    return {
        "type": "image",
        "image_url": "https://camo.githubusercontent.com/dc0e67c1884b3629ad73259f7f32ffcadcf974b4c92a1ebb9eaa2ffd0cfb2825/68747470733a2f2f646f637161692e6769746875622e696f2f646f63712f6173736574732f646f63712d646961672d6e6f76323032332e706e67",
        "alt_text": "Docq overview"
    }

@slack.slack_app.event("app_home_opened")
def handle_app_home_opened_events(ack: Callable, client: WebClient, event: Any) -> None:
    """Handle app home opened events."""
    ack()
    client.views_publish(
        user_id=event["user"],
        view={
            "type": "home",
            "blocks": [
                get_header_block(),
                get_divider_block(),
                get_context_block(),
                get_image_block(),
            ],
        }
    )
