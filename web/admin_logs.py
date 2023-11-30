"""Page: Admin / View Logs."""

import streamlit as st
from docq.config import LogType
from utils.layout import auth_required, list_logs_ui, render_page_title_and_favicon

render_page_title_and_favicon()
auth_required(requiring_selected_org_admin=True)

types_ = [LogType.ACTIVITY, LogType.SYSTEM]
tabs = st.tabs([t.value for t in types_])
for tab, type_ in zip(tabs, types_, strict=True):
    with tab:
        st.subheader(type_.value)
        list_logs_ui(type_)
