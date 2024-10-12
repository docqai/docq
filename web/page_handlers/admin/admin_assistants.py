"""Page: Admin / Manage Orgs."""

import streamlit as st
from docq.manage_assistants import list_assistants
from docq.support.store import _DataScope
from utils.layout import tracer
from utils.layout_assistants import (
    render_assistant_create_edit_ui,
    render_assistants_listing_ui,
    render_assistants_selector_ui,
    render_datascope_selector_ui,
)
from utils.sessions import get_selected_org_id


@tracer.start_as_current_span("admin_assistants_page")
def admin_assistants_page() -> None:
    """Page: Admin / Manage Assistants."""
    datascope = render_datascope_selector_ui()
    current_org_id = None
    if datascope == _DataScope.ORG:
        current_org_id = get_selected_org_id()
        if current_org_id is None:
            st.error("Please select an organisation")
            st.stop()
        st.write(f"Selected Organisation: {current_org_id}")

    assistants_data = list_assistants(org_id=current_org_id)

    render_assistants_selector_ui(assistants_data=assistants_data)
    with st.expander("+New Assistant", expanded=False):
        render_assistant_create_edit_ui(current_org_id)

    render_assistants_listing_ui(assistants_data=assistants_data, org_id=current_org_id)