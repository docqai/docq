"""Admin Section."""

import streamlit as st
from utils.layout import auth_required, render_page_title_and_favicon
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_section", attributes=baggage_as_attributes()):
    render_page_title_and_favicon()
    auth_required(requiring_selected_org_admin=True)

    orgs, users, user_groups, spaces, space_groups, logs, settings= st.tabs(
        ["Orgs", "Users", "User Groups", "Spaces", "Space Groups", "Logs", "Settings"]
    )

    with logs:
        import web.admin.admin_logs

    with settings:
        import web.admin.admin_settings

    with orgs:
        import web.admin.admin_orgs

    with users:
        import web.admin.admin_users

    with user_groups:
        import web.admin.admin_user_groups

    with spaces:
        import web.admin.admin_spaces

    with space_groups:
        import web.admin.admin_space_groups
