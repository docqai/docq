"""Page: Admin / View Logs."""

import streamlit as st
from docq.config import LogType
from st_pages import add_page_title
from utils.layout import auth_required, list_logs_ui, run_page_scripts, setup_page_scripts

setup_page_scripts()

auth_required(requiring_admin=True)

add_page_title()

types_ = [LogType.ACTIVITY, LogType.SYSTEM]
tabs = st.tabs([t.value for t in types_])
for tab, type_ in zip(tabs, types_, strict=True):
    with tab:
        st.subheader(type_.value)
        list_logs_ui(type_)

run_page_scripts()
