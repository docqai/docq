"""Page: Admin / Manage Users."""

import logging

import streamlit as st
from st_pages import add_page_title
from utils.layout import auth_required, create_user_ui, list_users_ui, org_selection_ui
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_users_page", attributes=baggage_as_attributes()):
    auth_required(requiring_selected_org_admin=True)

    add_page_title()

    with st.sidebar:
        org_selection_ui()

    create_user_ui()
    list_users_ui()
