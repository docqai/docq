"""Slack application request handlers.

These are the web API routes defined by Slack for the Slack integration.
"""

from docq.integrations.slack.slack_application import slack_app
from slack_bolt.adapter.tornado import SlackEventsHandler, SlackOAuthHandler

from web.api.base_handlers import BaseRequestHandler
from web.utils.streamlit_application import st_app


@st_app.api_route("/api/integration/slack/v1/events", dict(app=slack_app))
class SlackEventHandler(SlackEventsHandler, BaseRequestHandler):
    """Handle /slack/events requests."""


@st_app.api_route("/api/integration/slack/v1/install", dict(app=slack_app))
class SlackInstallHandler(SlackOAuthHandler, BaseRequestHandler):
    """Handle /slack/install requests."""


@st_app.api_route("/api/integration/slack/v1/oauth_redirect", dict(app=slack_app))
class SlackOAuthRedirectHandler(SlackOAuthHandler, BaseRequestHandler):
    """Handle /slack/oauth_redirect requests."""
