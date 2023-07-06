"""Page: Admin Overview."""

import streamlit as st
from st_pages import add_page_title
from utils.layout import auth_required, create_space_ui, list_spaces_ui, system_settings_ui

auth_required(requiring_admin=True)

add_page_title()

tab_settings, tab_spaces = st.tabs(["System Settings", "Shared Spaces"])

with tab_settings:
    system_settings_ui()

with tab_spaces:
    create_space_ui()
    list_spaces_ui(True)
