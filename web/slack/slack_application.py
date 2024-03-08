"""Slack event."""
from slack_bolt import App
from slack_bolt.adapter.tornado import SlackEventsHandler

from web.api.base_handlers import BaseRequestHandler
from web.utils.streamlit_application import st_app

slack_app = App()


@st_app.api_route("/slack/events", dict(app=slack_app))
class SlackEventHandler(SlackEventsHandler, BaseRequestHandler):
    """Handle /slack/events requests."""
