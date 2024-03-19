"""Slack install handler."""

import streamlit as st

from web.utils.handlers import handle_add_slack_integration
from web.utils.layout import auth_required, render_integrations, render_slack_channels, render_slack_installation_button

integrations = [
    {
        "name": "Slack",
        "description": "Slack is a business communication platform that allows teams to communicate and collaborate.",
        "icon": "slack",
        "url": "/api/integration/slack/v1/install",
    },
    {
        "name": "Teams",
        "description": "Google Drive is a file storage and synchronization service developed by Google.",
        "icon": "google-drive",
        "url": "/api/integration/google-drive/v1/install",
    }
]


auth_required(requiring_selected_org_admin=True)

st.title("Integrations")

integration = st.selectbox(
    "Select an integration to get started",
    options=[integration["name"] for integration in integrations],
)

if integration == "Slack":
    render_slack_installation_button()

    render_integrations()

    st.divider()
    st.write("### Channels")
    render_slack_channels()

else:
    st.info("Coming soon! :construction:")
