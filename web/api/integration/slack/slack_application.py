"""Slack event."""
import os

from docq.support.store import get_sqlite_shared_system_file
from slack_bolt import App, BoltResponse
from slack_bolt.adapter.tornado import SlackEventsHandler, SlackOAuthHandler
from slack_bolt.oauth.callback_options import CallbackOptions, FailureArgs, SuccessArgs

from web.api.base_handlers import BaseRequestHandler
from web.utils.streamlit_application import st_app

from .oauth_flow import SlackOAuthFlow

CLIENT_ID = os.environ.get("SLACK_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SLACK_CLIENT_SECRET")
SCOPES = ["app_mentions:read", "im:history", "chat:write", "channels:read", "groups:read", "im:read", "mpim:read"]
USER_SCOPES = ["admin"]

def success_callback(success_args: SuccessArgs) -> BoltResponse:
    """Success callback."""
    return success_args.default.success(success_args)


def failure_callback(failure_args: FailureArgs) -> BoltResponse:
    """Failure callback."""
    return failure_args.default.failure(failure_args)


slack_app = App(
    process_before_response=True,
    oauth_flow=SlackOAuthFlow.sqlite3(
        database=get_sqlite_shared_system_file(),
        install_path="/api/integration/slack/v1/install",
        redirect_uri_path="/api/integration/slack/v1/oauth_redirect",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES,
        user_scopes=USER_SCOPES,
        callback_options=CallbackOptions(success=success_callback, failure=failure_callback),
    )
)


@st_app.api_route("/api/integration/slack/v1/events", dict(app=slack_app))
class SlackEventHandler(SlackEventsHandler, BaseRequestHandler):
    """Handle /slack/events requests."""

@st_app.api_route("/api/integration/slack/v1/install", dict(app=slack_app))
class SlackInstallHandler(SlackOAuthHandler, BaseRequestHandler):
    """Handle /slack/install requests."""

@st_app.api_route("/api/integration/slack/v1/oauth_redirect", dict(app=slack_app))
class SlackOAuthRedirectHandler(SlackOAuthHandler, BaseRequestHandler):
    """Handle /slack/oauth_redirect requests."""
