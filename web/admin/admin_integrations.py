"""Slack install handler."""

import streamlit as st

from web.utils.layout import render_integrations, render_slack_installation_button, tracer


@tracer.start_as_current_span("admin_integrations_page")
def admin_integrations_page() -> None:
    """Admin integrations section."""
    integrations = [
        {
            "name": "Slack",
            "description": "Slack the business communication platform that allows teams to communicate and collaborate.",
            "icon": "slack",
            "url": "/api/integration/slack/v1/install",
        },
        {
            "name": "MS Teams",
            "description": "Mircosoft Teams the business communication platform that allows teams to communicate and collaborate.",
            "icon": "google-drive",
            "url": "/api/integration/msteams/v1/install",
        },
    ]

    integration = st.selectbox(
        "Select an integration",
        options=[integration["name"] for integration in integrations],
    )

    if integration == "Slack":
        render_slack_installation_button()

        render_integrations()

    else:
        st.info("Coming soon!")
