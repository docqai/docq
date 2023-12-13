"""Page: Admin / View Logs."""

import streamlit as st
from docq.config import LogType
from utils.layout import list_logs_ui, tracer


@tracer.start_as_current_span("admin_logs_page")
def admin_logs_page() -> None:
    """Page: Admin / View Logs."""
    types_ = [LogType.ACTIVITY, LogType.SYSTEM]
    tabs = st.tabs([t.value for t in types_])
    for tab, type_ in zip(tabs, types_, strict=True):
        with tab:
            st.subheader(type_.value)
            list_logs_ui(type_)
