"""Page: Admin / Manage Users."""

import streamlit as st
from st_pages import add_page_title
from utils.layout import auth_required, create_user_ui, list_users_ui, org_selection_ui

auth_required(requiring_admin=True)

add_page_title()

with st.sidebar:
    org_selection_ui()

create_user_ui()
list_users_ui()
