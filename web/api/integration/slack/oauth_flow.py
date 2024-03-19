""""Custom slack oauth flow."""

from typing import Self

from docq.integrations.slack import create_docq_slack_installation
from docq.support.auth_utils import get_cache_auth_session
from slack_bolt.oauth.oauth_flow import OAuthFlow
from slack_bolt.request import BoltRequest
from slack_sdk.oauth.installation_store import Installation

from web.utils.constants import SessionKeyNameForAuth


class SlackOAuthFlow(OAuthFlow):
    """Custom slack oauth flow."""

    def save_docq_slack_installation(self: Self, installation: Installation) -> None:
        """Save a Docq slack installation."""
        auth_session = get_cache_auth_session()
        if  auth_session is not None:
            selected_org_id = auth_session.get(SessionKeyNameForAuth.SELECTED_ORG_ID.name)
            if selected_org_id is not None:
                create_docq_slack_installation(installation, int(selected_org_id))
            else:
                raise Exception("Not Authenticated.")

    def store_installation(self: Self, request: BoltRequest, installation: Installation) -> None:
        """Store an installation."""
        # may raise BoltError
        self.save_docq_slack_installation(installation)
        self.settings.installation_store.save(installation)
