"""Slack application."""

import logging
import os

from docq.integrations.slack.slack_oauth_flow import SlackOAuthFlow
from docq.support.store import get_sqlite_shared_system_file
from opentelemetry import trace
from slack_bolt import App, BoltResponse
from slack_bolt.oauth.callback_options import CallbackOptions, FailureArgs, SuccessArgs

from ...config import ENV_VAR_DOCQ_SLACK_CLIENT_ID, ENV_VAR_DOCQ_SLACK_CLIENT_SECRET, ENV_VAR_DOCQ_SLACK_SIGNING_SECRET

tracer = trace.get_tracer(__name__)

CLIENT_ID = os.environ.get(ENV_VAR_DOCQ_SLACK_CLIENT_ID)
CLIENT_SECRET = os.environ.get(ENV_VAR_DOCQ_SLACK_CLIENT_SECRET)
SIGNING_SECRET = os.environ.get(ENV_VAR_DOCQ_SLACK_SIGNING_SECRET)
SCOPES = ["app_mentions:read", "im:history", "chat:write", "channels:read", "groups:read", "im:read", "mpim:read"]
USER_SCOPES = []  # OAuth scopes to request if the bot needs to take actions on behalf of the user. Docq doesn't need to do this right now.


@tracer.start_as_current_span(name="slack_success_callback")
def success_callback(success_args: SuccessArgs) -> BoltResponse:
    """Success callback."""
    return success_args.default.success(success_args)

@tracer.start_as_current_span(name="slack_failure_callback")
def failure_callback(failure_args: FailureArgs) -> BoltResponse:
    """Failure callback."""
    span = trace.get_current_span()
    span.set_attribute("slack_failure_callback_args", str(failure_args))
    return failure_args.default.failure(failure_args)

with tracer.start_as_current_span(name="initialise_slack_app") as slack_app_span:
    slack_app_span.set_attributes(
        {
            ENV_VAR_DOCQ_SLACK_CLIENT_ID: CLIENT_ID if CLIENT_ID else "value missing",
            ENV_VAR_DOCQ_SLACK_CLIENT_SECRET: "value present" if CLIENT_SECRET else "value missing",
            ENV_VAR_DOCQ_SLACK_SIGNING_SECRET: "value present" if SIGNING_SECRET else "value missing",
        }
    )
    if CLIENT_ID and CLIENT_SECRET and SIGNING_SECRET:
        slack_app = App(
            process_before_response=True,
            request_verification_enabled=True,
            signing_secret=SIGNING_SECRET,
            oauth_flow=SlackOAuthFlow.sqlite3(
                database=get_sqlite_shared_system_file(),
                install_path="/api/integration/slack/v1/install",
                redirect_uri_path="/api/integration/slack/v1/oauth_redirect",
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                scopes=SCOPES,
                user_scopes=USER_SCOPES,
                callback_options=CallbackOptions(success=success_callback, failure=failure_callback),
            ),
        )
    else:
        slack_app_span.record_exception(
            ValueError(
                f"One or more Slack environment variables are not set. Expected env var names: {ENV_VAR_DOCQ_SLACK_CLIENT_ID}, {ENV_VAR_DOCQ_SLACK_CLIENT_SECRET}, {ENV_VAR_DOCQ_SLACK_SIGNING_SECRET}. Values for these are part of your app config in Slack."
            )
        )
        slack_app_span.set_status(trace.StatusCode.ERROR)
        logging.error(
            f"One or more Slack environment variables are not set. Expected env var names: {ENV_VAR_DOCQ_SLACK_CLIENT_ID}, {ENV_VAR_DOCQ_SLACK_CLIENT_SECRET}, {ENV_VAR_DOCQ_SLACK_SIGNING_SECRET}. Values for these are part of your app config in Slack."
        )
        # raise ValueError("Slack client ID and client secret must be set in the environment.")
