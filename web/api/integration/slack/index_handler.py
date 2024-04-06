"""Slack application package init file."""

import json
import logging
from typing import Self

from opentelemetry import trace

from web.utils.streamlit_application import st_app

from ...base_handlers import BaseRequestHandler

tracer = trace.get_tracer(__name__)
with tracer.start_as_current_span("slack_integration_register_api_handlers") as span:
    try:
        from docq.integrations.slack.slack_application import slack_app

        from . import app_home, chat_handler, slack_request_handlers

        __all__ = ["chat_handler", "app_home", "slack_request_handlers"]
        span.add_event("Successfully registered Slack integration API handlers.")
    except ImportError as e:
        span.record_exception(e)
        span.set_status(
            trace.StatusCode.ERROR,
            "Was unable to initialise the Slack integration. Check configuration and environment variables.",
        )
        logging.error(
            "Was unable to initialise the Slack integration. Check configuration and environment variables. %s", e
        )

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
