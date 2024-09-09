"""Streamlit entry point for the web app."""

import docq
import streamlit as st
from streamlit.navigation.page import StreamlitPage
from utils.layout import (
    __logout_button,
    init_with_pretty_error_ui,
    org_selection_ui,
    production_layout,
)
from utils.observability import baggage_as_attributes, tracer
from utils.sessions import is_current_user_authenticated, is_current_user_selected_org_admin
from utils.streamlit_application import st_app
from utils.streamlit_page_extension import StreamlitPageExtension as StPage

#### DO NOT REMOVE THIS IMPORT ####
import web.api.index_handler as h  # noqa: F401

h.setup()
####

st_app.print_registered_routes()

with tracer().start_as_current_span("index", attributes=baggage_as_attributes()):
    init_with_pretty_error_ui()
    production_layout()

    with st.sidebar:
        st.logo(image="web/static/docq-v2_1-word-mark.jpg")
        org_selection_ui()

    public_access = [
        StPage(page="page_handlers/home.py", title="Home", default=True),
        StPage(page="page_handlers/signup.py", title="Docq Signup", url_path="signup", hidden=True),
        StPage(page="page_handlers/verify.py", title="Verify", url_path="verify", hidden=True),
        StPage(page="page_handlers/embed.py", title="widget", hidden=True),
    ]

    authenticated_access = [
        StPage(page="page_handlers/personal_chat.py", title="General Chat", url_path="General_Chat"),
        StPage(page="page_handlers/shared_ask.py", title="Ask Shared Documents", url_path="Ask_Shared_Documents"),
        StPage(page="page_handlers/shared_spaces.py", title="List Shared Spaces", url_path="List_Shared_Spaces"),
    ]

    org_admin_access = [
        StPage(
            page="page_handlers/admin_spaces.py", title="Admin_Spaces", url_path="Admin_Spaces", hidden=True
        ),  # Do not remove: This is used as the G Drive data source integration auth redirect page
        StPage(page="page_handlers/admin/index.py", title="Admin Section", url_path="Admin_Section", icon="💂"),
        "🤖&nbsp;&nbsp;Tools",
        StPage(page="page_handlers/ml_eng_tools/assistants.py", title="Assistants", url_path="Assistants"),
        StPage(
            page="page_handlers/ml_eng_tools/visualise_index.py",
            title="Visualise Index",
            url_path="Visualise_Index",
        ),
        StPage(page="page_handlers/ml_eng_tools/rag.py", title="RAG", url_path="RAG"),
        StPage(
            page="page_handlers/ml_eng_tools/visualise_agent_messages.py",
            title="Visualise Agent Messages",
            url_path="Visualise_Agent_Messages",
        ),
    ]

    pages = []
    pages.extend(public_access)

    if is_current_user_authenticated():
        pages.extend(authenticated_access)

    if is_current_user_selected_org_admin():
        pages.extend(org_admin_access)

    sidebar = st.sidebar

    # TODO: this can move into a component function
    for page in pages:
        if isinstance(page, str):  # handle section headers. TODO: change this to a class with icon etc.
            sidebar.write("&nbsp;&nbsp;" + page)

        if isinstance(page, StPage):  # noqa: SIM102
            if not page.hidden:
                sidebar.page_link(page, icon=page.icon if page.icon else None)

    pages = [page for page in pages if isinstance(page, StreamlitPage)]  # remove the section headers
    pg = st.navigation(
        pages=pages,  # type: ignore
        position="hidden",
    )
    if is_current_user_authenticated():
        st.sidebar.divider()
        sidebar_dynamic_section = sidebar.container()
        # hold a reference in session state so we can add elements to the sidebar
        # in between the menu options and logout button from other pages.
        st.session_state["sidebar_dynamic_section"] = sidebar_dynamic_section
        st.sidebar.divider()

        __logout_button()
        st.sidebar.write(f"v{docq.__version_str__}")

    pg.run()
