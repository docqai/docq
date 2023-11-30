"""Page: Admin / Manage Users."""


import streamlit as st
from utils.layout import (
    auth_required,
    create_user_ui,
    list_users_ui,
    org_selection_ui,
    render_page_title_and_favicon,
)
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_users_page", attributes=baggage_as_attributes()):
    render_page_title_and_favicon()
    auth_required(requiring_selected_org_admin=True)

    with st.sidebar:
        org_selection_ui()

    create_user_ui()
    list_users_ui()
