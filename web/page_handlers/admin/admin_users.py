"""Page: Admin / Manage Users."""


import streamlit as st
from utils.layout import create_user_ui, list_users_ui, org_selection_ui, tracer


@tracer.start_as_current_span("admin_users_page")
def admin_users_page() -> None:
    """Page: Admin / Manage Users."""
    with st.sidebar:
        org_selection_ui()

    create_user_ui()
    list_users_ui()
