"""Page: Admin / View Logs."""

import streamlit as st
from docq.config import LogType
from st_pages import add_page_title
from utils.layout import auth_required, list_logs_ui

auth_required(requiring_admin=True)

add_page_title()

tab_activity, tab_system = st.tabs(["Activity Logs", "System Logs"])


with tab_activity:
    st.subheader("Activities")
    list_logs_ui(LogType.ACTIVITY)

with tab_system:
    st.subheader("System")
    list_logs_ui(LogType.SYSTEM)
