"""Page: Home (no auth required)."""


import streamlit as st

#from docq_extensions.web.layout import subscriptions
from st_pages import Page, Section, show_pages
from utils.layout import (
    auth_required,
    init_with_pretty_error_ui,
    org_selection_ui,
    production_layout,
    public_access,
    render_page_title_and_favicon,
)
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("home_page", attributes=baggage_as_attributes()):
    render_page_title_and_favicon()
    init_with_pretty_error_ui()
    production_layout()

    with st.sidebar:
        org_selection_ui()

    show_pages(
        [
            Page("web/index.py", "Home", "🏠"),
            Page("web/signup.py", "signup"),
            Page("web/verify.py", "verify"),
            Page("web/personal_chat.py", "General_Chat"),
            Page("web/shared_ask.py", "Ask_Shared_Documents"),
            Page("web/shared_spaces.py", "List_Shared_Spaces"),
            Page("web/embed.py", "widget"),
            Page("web/admin/index.py", "Admin_Section", icon="💂"),
            Section("ML Engineering", icon="💻"),
            Page("web/ml_eng_tools/visualise_index.py", "Visualise Index"),
            Page("web/ml_eng_tools/visualise_agent_messages.py", "Visualise Agent Messages"),
        ]
    )

    public_access()

    login_container = st.container()

    st.subheader("Welcome to Docq - Private & Secure AI Knowledge Insight, your second brain.")

    st.markdown(
        """
    - Click on _General Chat_ to use Docq like ChatGPT.
    - Click on _Ask Shared Documents_ link to ask questions and get answers from documents shared within your organisation as a Space.
    - Click on _Admin Spaces_ to create a new Space, add documents, and share with your organisation.
    """
    )

    st.subheader("Tips & Tricks")
    st.markdown(
        """
    - Always ask questions in plain English and try to be as specific as possible.
    - Admins can manage the documents in a Space which sets the context for your questions.
    - Your access to shared spaces is subject to permissions set by your organisation admin.
    - For any questions or feedback, please contact your organisation's Docq administrator.

    Enjoy Docq!
    """
    )


    st.markdown(
        """
    [Website](https://docq.ai) | [Docs](https://docqai.github.io/docq/) | [Github](https://github.com/docqai) | [Twitter](https://twitter.com/docqai)
        """
    )


    with login_container:
        auth_required(show_login_form=True, requiring_selected_org_admin=False, show_logout_button=True)
