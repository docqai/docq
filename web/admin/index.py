"""Admin Section."""

import streamlit as st
from utils.layout import auth_required, render_page_title_and_favicon
from utils.observability import baggage_as_attributes, tracer
from utils.sessions import is_current_user_selected_org_admin, is_current_user_super_admin

from web.admin.admin_integrations import admin_integrations_page
from web.admin.admin_logs import admin_logs_page
from web.admin.admin_orgs import admin_orgs_page
from web.admin.admin_settings import admin_settings_page
from web.admin.admin_space_groups import admin_space_groups_page
from web.admin.admin_spaces import admin_spaces_page
from web.admin.admin_user_groups import admin_user_groups_page
from web.admin.admin_users import admin_users_page


def super_and_org_admin_pages() -> None:
    """Sections if both super admin and current selected org admin."""
    (
        admin_orgs,
        admin_users,
        admin_user_groups,
        admin_spaces,
        admin_space_groups,
        admin_settings,
        admin_chat_integrations,
        admin_logs,
    ) = st.tabs(["Orgs", "Users", "User Groups", "Spaces", "Space Groups", "Settings", "Chat Integrations", "Logs"])




    with admin_orgs:
        admin_orgs_page()

    with admin_users:
        admin_users_page()

    with admin_user_groups:
        admin_user_groups_page()

    with admin_spaces:
        admin_spaces_page()

    with admin_space_groups:
        admin_space_groups_page()

    with admin_settings:
        admin_settings_page()

    with admin_chat_integrations:
        admin_integrations_page()

    with admin_logs:
        admin_logs_page()


def org_admin_pages() -> None:
    """Sections if only org admin."""
    (
        admin_orgs,
        admin_users,
        admin_user_groups,
        admin_spaces,
        admin_space_groups,
        admin_settings,
        admin_chat_integrations,
        admin_logs,
    ) = st.tabs(["Org", "Users", "User Groups", "Spaces", "Space Groups", "Settings", "Chat Integrations", "Logs"])

    with admin_orgs:
        admin_orgs_page()

    with admin_users:
        admin_users_page()

    with admin_user_groups:
        admin_user_groups_page()

    with admin_spaces:
        admin_spaces_page()

    with admin_space_groups:
        admin_space_groups_page()

    with admin_settings:
        admin_settings_page()

    with admin_chat_integrations:
        admin_integrations_page()

    with admin_logs:
        admin_logs_page()


def super_admin_pages() -> None:
    """Sections if only super admin."""
    (
        admin_orgs,
        admin_users,
        admin_settings,
    ) = st.tabs(
        [
            "Orgs",
            "Users",
            "Settings",
        ]
    )

    with admin_settings:
        admin_settings_page()

    with admin_orgs:
        admin_orgs_page()

    with admin_users:
        admin_users_page()


with tracer().start_as_current_span("admin_section", attributes=baggage_as_attributes()) as span:
    render_page_title_and_favicon()
    auth_required(requiring_selected_org_admin=True)

    if is_current_user_super_admin() and is_current_user_selected_org_admin():
        # st.write("You are a _super admin_ and _current selected org admin_.")
        span.set_attribute("user_role", "super_admin_and_org_admin")
        super_and_org_admin_pages()
    elif is_current_user_selected_org_admin:
        span.set_attribute("user_role", "org_admin_only")
        org_admin_pages()
    elif is_current_user_super_admin():
        span.set_attribute("user_role", "super_admin_only")
        super_admin_pages()
