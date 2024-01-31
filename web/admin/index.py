"""Admin Section."""

import streamlit as st
from utils.layout import auth_required, render_page_title_and_favicon
from utils.observability import baggage_as_attributes, tracer
from utils.sessions import is_current_user_super_admin

from web.admin.admin_logs import admin_logs_page
from web.admin.admin_orgs import admin_orgs_page
from web.admin.admin_settings import admin_settings_page
from web.admin.admin_space_groups import admin_space_groups_page
from web.admin.admin_spaces import admin_spaces_page
from web.admin.admin_user_groups import admin_user_groups_page
from web.admin.admin_users import admin_users_page


def admin_pages() -> None:
    """Admin Section."""
    admin_orgs, admin_users, admin_user_groups, admin_spaces, admin_space_groups, admin_logs, admin_settings= st.tabs(
        ["Admin Orgs", "Admin Users", "Admin User Groups", "Admin Spaces", "Admin Space Groups", "Admin Logs", "Admin Settings"]
    )

    with admin_logs:
        admin_logs_page()

    with admin_settings:
        admin_settings_page()

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


def user_admin_pages() -> None:
    """Admin Section."""
    admin_spaces, admin_space_groups, admin_logs, admin_settings = st.tabs(
        ["Admin Spaces", "Admin Space Groups", "Admin Logs", "Admin Settings"]
    )
    with admin_logs:
        admin_logs_page()

    with admin_settings:
        admin_settings_page()

    with admin_spaces:
        admin_spaces_page()

    with admin_space_groups:
        admin_space_groups_page()


with tracer().start_as_current_span("admin_section", attributes=baggage_as_attributes()):
    render_page_title_and_favicon()
    auth_required(requiring_selected_org_admin=True)

    if is_current_user_super_admin():
        admin_pages()
    else:
        user_admin_pages()
