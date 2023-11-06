"""Page: Admin / Manage Users."""

import logging

import streamlit as st
from st_components.page_header import create_menu_items
from st_pages import add_page_title
from utils.layout import (
    auth_required,
    create_user_ui,
    list_users_ui,
    org_selection_ui,
    run_page_scripts,
    setup_page_scripts,
)

setup_page_scripts()
auth_required(requiring_admin=True)

add_page_title()

with st.sidebar:
    org_selection_ui()

create_user_ui()
list_users_ui()

run_page_scripts()
