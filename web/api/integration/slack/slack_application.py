"""Slack event."""
import os

from slack_bolt import App, BoltResponse
from slack_bolt.adapter.tornado import SlackEventsHandler, SlackOAuthHandler
from slack_bolt.oauth.callback_options import CallbackOptions, FailureArgs, SuccessArgs
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore

from web.api.base_handlers import BaseRequestHandler
from web.utils.streamlit_application import st_app


def success_callback(success_args: SuccessArgs) -> BoltResponse:
    """Success callback."""
    return success_args.default.success(success_args)

def failure_callback(failure_args: FailureArgs) -> BoltResponse:
    """Failure callback."""
    return failure_args.default.failure(failure_args)

slack_app = App(
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    installation_store=FileInstallationStore(),
    oauth_settings=OAuthSettings(
        client_id=os.environ.get("SLACK_CLIENT_ID"),
        client_secret=os.environ.get("SLACK_CLIENT_SECRET"),
        scopes=["app_mentions:read", "im:history", "chat:write"],
        user_scopes=["admin"],
        install_path="/api/integration/slack/v1/install",
        redirect_uri_path="/api/integration/slack/v1/oauth_redirect",
        installation_store=FileInstallationStore(),
        state_store=FileOAuthStateStore(expiration_seconds=300),
        callback_options=CallbackOptions(success=success_callback, failure=failure_callback),
    ),
)

@st_app.api_route("/api/integration/slack/v1/events", dict(app=slack_app))
class SlackEventHandler(SlackEventsHandler, BaseRequestHandler):
    """Handle /slack/events requests."""


@st_app.api_route("/api/integration/slack/v1/install", dict(app=slack_app))
class SlackInstallHandler(SlackOAuthHandler):
    """Handle /slack/install requests."""


@st_app.api_route("/api/integration/slack/v1/oauth_redirect", dict(app=slack_app))
class SlackOAuthRedirectHandler(SlackOAuthHandler):
    """Handle /slack/oauth_redirect requests."""
