"""Page: Admin / View Logs."""

import streamlit as st
from docq.config import LogType
from utils.layout import list_logs_ui

types_ = [LogType.ACTIVITY, LogType.SYSTEM]
tabs = st.tabs([t.value for t in types_])
for tab, type_ in zip(tabs, types_, strict=True):
    with tab:
        st.subheader(type_.value)
        list_logs_ui(type_)
