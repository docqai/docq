""""Custom slack oauth flow."""

# import html
import os
from logging import Logger
from typing import Optional, Self, Sequence

from docq.integrations.slack.manage_slack import create_docq_slack_installation
from slack_bolt.error import BoltError
from slack_bolt.oauth.callback_options import CallbackOptions
from slack_bolt.oauth.oauth_flow import OAuthFlow
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_bolt.request import BoltRequest
from slack_sdk.oauth import OAuthStateUtils
from slack_sdk.oauth.installation_store import Installation
from slack_sdk.oauth.installation_store.sqlite3 import SQLite3InstallationStore
from slack_sdk.oauth.state_store.sqlite3 import SQLite3OAuthStateStore
from slack_sdk.web import WebClient


class SlackOAuthFlow(OAuthFlow):
    """Custom slack oauth flow."""

    @classmethod
    def sqlite3(
        cls,  # noqa: ANN102
        database: str,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scopes: Optional[Sequence[str]] = None,
        user_scopes: Optional[Sequence[str]] = None,
        redirect_uri: Optional[str] = None,
        install_path: Optional[str] = None,
        redirect_uri_path: Optional[str] = None,
        callback_options: Optional[CallbackOptions] = None,
        success_url: Optional[str] = None,
        failure_url: Optional[str] = None,
        authorization_url: Optional[str] = None,
        state_cookie_name: str = OAuthStateUtils.default_cookie_name,
        state_expiration_seconds: int = OAuthStateUtils.default_expiration_seconds,
        installation_store_bot_only: bool = False,
        token_rotation_expiration_minutes: int = 120,
        client: Optional[WebClient] = None,
        logger: Optional[Logger] = None,
    ) -> "SlackOAuthFlow":
        """Create a SlackOAuthFlow."""
        client_id = client_id or os.environ["SLACK_CLIENT_ID"]
        client_secret = client_secret or os.environ["SLACK_CLIENT_SECRET"]
        scopes = scopes or os.environ.get("SLACK_SCOPES", "").split(",")
        user_scopes = user_scopes or os.environ.get("SLACK_USER_SCOPES", "").split(",")
        redirect_uri = redirect_uri or os.environ.get("SLACK_REDIRECT_URI")
        return SlackOAuthFlow(
            client=client or WebClient(),
            logger=logger,
            settings=OAuthSettings(
                client_id=client_id,
                client_secret=client_secret,
                scopes=scopes,
                user_scopes=user_scopes,
                redirect_uri=redirect_uri,
                install_path=install_path,  # type: ignore
                redirect_uri_path=redirect_uri_path,  # type: ignore
                callback_options=callback_options,
                success_url=success_url,
                failure_url=failure_url,
                authorization_url=authorization_url,
                installation_store=SQLite3InstallationStore(
                    database=database,
                    client_id=client_id,
                    logger=logger,  # type: ignore
                ),
                installation_store_bot_only=installation_store_bot_only,
                token_rotation_expiration_minutes=token_rotation_expiration_minutes,
                state_store=SQLite3OAuthStateStore(
                    database=database,
                    expiration_seconds=state_expiration_seconds,
                    logger=logger,  # type: ignore
                ),
                state_cookie_name=state_cookie_name,
                state_expiration_seconds=state_expiration_seconds,
            ),
        )

    def get_cookie(self: Self, name: str, cookies: Optional[str | Sequence[str]]) -> Optional[str]:
        """Get a cookie."""
        from docq.support.auth_utils import decrypt_cookie_value

        if not cookies:
            return None

        if isinstance(cookies, str):
            cookies = [cookies]
        for cookie in cookies:
            for item in cookie.split(";"):
                key, value = item.split("=", 1)
                if key.strip() == name:
                    return decrypt_cookie_value(value)
        return None

    def save_docq_slack_installation(self: Self, request: BoltRequest, installation: Installation) -> None:
        """Save a Docq slack installation."""
        docq_slack_app_state =  self.get_cookie("docq_slack_app_state", request.headers.get("cookie"))
        if docq_slack_app_state is not None:
            _, selected_org_id = docq_slack_app_state.split(":")
            create_docq_slack_installation(installation, int(selected_org_id))
        else:
            raise BoltError("Login to Docq before installing the slack app.")

    def store_installation(self: Self, request: BoltRequest, installation: Installation) -> None:
        """Store an installation."""
        self.save_docq_slack_installation(request, installation)
        self.settings.installation_store.save(installation)

    # NOTE: This only shows how to create a custom installation page if not provided the default one from slack is used.
    # def build_install_page_html(self: Self, url: str, request: BoltRequest) -> str:
    #     """Build the installation page html."""
    #     return f"""
    #         <html>
    #           <head>
    #           <link rel="icon" href="data:,">
    #           <style>
    #             body {{
    #               padding: 10px 15px;
    #               font-family: verdana;
    #               text-align: center;
    #             }}
    #           </style>
    #          </head>
    #          <body>
    #           <h2>Docq Slack App Installation</h2>
    #           <p><a href="{html.escape(url)}"><img alt=""Add to Slack"" height="40" width="139" src="https://platform.slack-edge.com/img/add_to_slack.png" srcset="https://platform.slack-edge.com/img/add_to_slack.png 1x, https://platform.slack-edge.com/img/add_to_slack@2x.png 2x" /></a></p>
    #           </body>
    #         </html>
    #     """
