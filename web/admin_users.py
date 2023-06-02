"""Page: Admin / Manage Users."""

import streamlit as st
from st_pages import add_page_title
from utils.layout import auth_required, create_user_ui, list_users_ui

add_page_title()

auth_required(requiring_admin=True)

tab_list, tab_create = st.tabs(["List All Users", "Create New User"])


with tab_list:
    st.subheader("List")
    list_users_ui()

with tab_create:
    st.subheader("Create")
    create_user_ui()
