"""Slack application package init file."""

import json
import logging
from typing import Self

from opentelemetry import trace

from web.utils.streamlit_application import st_app

from ...base_handlers import BaseRequestHandler

try:
    from docq.integrations.slack.slack_application import slack_app

    from . import app_home, chat_handler, slack_request_handlers

    __all__ = ["chat_handler", "app_home", "slack_request_handlers"]
except ImportError:
    trace.get_current_span().record_exception(
        ImportError("Was unable to initialise the Slack integration. Check configuration and environment variables.")
    )
    logging.error("Was unable to initialise the Slack integration. Check configuration and environment variables.")

    @st_app.api_route("/api/integration/slack/v1/events")
    class SlackEventHandler(BaseRequestHandler):
        """Handle /slack/events when the Slack integration is not available.

        We do this to avoid silent failures and to help troubleshoot by logging the messages below.
        This is a hack mainly because how we hook into the Streamlit Tornado instance to add API route handlers.
        """

        def post(self: Self) -> None:
            """Handle GET request."""
            payload = json.loads(self.request.body.decode())
            logging.warning(
                "This is a Slack bot request that was unhandled. The Slack integration is not available. Likely due to a configuration error. From Slack Team ID: %s",
                payload.get("team_id"),
            )

            trace.get_current_span().add_event("Unhandled Slack bot request")
            trace.get_current_span().set_status(
                trace.StatusCode.ERROR,
                "This is a Slack bot request that was unhandled. The Slack integration is not available. Likely due to a configuration error.",
            )
