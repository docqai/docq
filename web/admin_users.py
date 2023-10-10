"""Page: Admin / Manage Users."""
import st_components.page_header as st_header
import streamlit as st
from st_pages import add_page_title
from utils.layout import auth_required, create_user_ui, list_users_ui, org_selection_ui

st_header._setup_page_script()
auth_required(requiring_admin=True)

add_page_title()

with st.sidebar:
    org_selection_ui()

create_user_ui()
list_users_ui()

st_header.run_script()
