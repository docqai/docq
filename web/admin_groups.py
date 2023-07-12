"""Page: Admin / Manage Users."""

import streamlit as st
from st_pages import add_page_title
from utils.layout import auth_required, create_group_ui, list_groups_ui

auth_required(requiring_admin=True)

add_page_title()

tab_list, tab_create = st.tabs(["List All Groups", "Create New Group"])


with tab_list:
    st.subheader("List")
    list_groups_ui()

with tab_create:
    st.subheader("Create")
    create_group_ui()
