"""Streamlit entry point for the web app."""

import streamlit as st

# from docq_extensions.web.layout import subscriptions
from utils.handlers import (
    handle_fire_extensions_callbacks,  # noqa F401 don't remove this line, it's used to register api routes
)
from utils.layout import (
    auth_required,
    init_with_pretty_error_ui,
    org_selection_ui,
    production_layout,
    public_access,
    render_docq_logo,
    render_page_title_and_favicon,
)
from utils.observability import baggage_as_attributes, tracer

import web.api.index_handler  # noqa F401 don't remove this line, it's used to register api routes

with tracer().start_as_current_span("index", attributes=baggage_as_attributes()):
    # render_docq_logo()

    # render_page_title_and_favicon(
    #     page_display_title=":violet[Your private ChatGPT alternative].",
    #     browser_title="Docq.AI - Private ChatGPT alternative.",
    # )

    init_with_pretty_error_ui()
    production_layout()

    print("Hello from index.py")

    with st.sidebar:
        org_selection_ui()

    pg = st.navigation(
        [
            st.Page(page="page_handlers/home.py", title=":violet[Your private ChatGPT alternative].", default=True),
            # st.Page(page="pages/signup.py", title="signup"),
            # st.Page(page="pages/verify.py", title="verify"),
            st.Page(page="page_handlers/personal_chat.py", title="General Chat", url_path="/general_chat"),
            # st.Page(page="pages/shared_ask.py", title="Ask_Shared_Documents"),
            # st.Page(page="pages/shared_spaces.py", title="List_Shared_Spaces"),
            # st.Page(page="pages/embed.py", title="widget"),
            # st.Page(
            #     page="pages/admin_spaces.py", title="Admin_Spaces"
            # ),  # Do not remove: This is used as the G Drive data source integration auth redirect page
            # st.Page(page="pages/admin/index.py", title="Admin_Section", icon="💂"),
            # st.Page(page="pages/ml_eng_tools/assistants.py", title="Assistants"),
            # st.Page(page="pages/ml_eng_tools/visualise_index.py", title="Visualise Index"),
            # st.Page(page="pages/ml_eng_tools/rag.py", title="RAG"),
            # st.Page(page="pages/ml_eng_tools/visualise_agent_messages.py", title="Visualise Agent Messages"),
        ]
    )

    pg.run()

    # public_access()

    # login_container = st.container()

    # st.subheader("Secure unlock knowledge from your confidential business documents.")

    # st.markdown("Upload a document. Ask questions. Get answers. It's that simple!")

    # st.subheader("Guide")
    # st.markdown(
    #     """
    # - **_General Chat_** to use Docq like ChatGPT.
    # - **_Ask Shared Documents_** to ask questions and get answers from documents shared within your organisation as a Space.
    # - **_Admin Section_ > _Admin Spaces_** to create a new Space, add documents, and share with your organisation.
    # """
    # )

    # st.subheader("Tips & Tricks")
    # st.markdown(
    #     """
    # - Always ask questions in plain English and try to be as specific as possible.
    # - Admins can manage the documents in a Space which sets the context for your questions.
    # - Every user also has a personal organisation so you can create Spaces that are personal knowledge repositories.
    # - Your access to shared spaces is subject to permissions set by your organisation admin.
    # - For any questions or feedback, please contact your organisation's Docq administrator.

    # Enjoy Docq!
    # """
    # )

    # st.divider()
    # st.markdown(
    #     """
    # [Website](https://docq.ai) | Star on [Github](https://github.com/docqai) | Follow on [Twitter](https://twitter.com/docqai)
    #     """
    # )

    # st.markdown(
    #     """
    # For help: [Docs](https://docqai.github.io/docq/) | Join [Slack](https://join.slack.com/t/docqai/shared_invite/zt-27p17lu6v-6KLJxSmt61vfNqCavSE73A) | Email [hi@docqai.com](mailto:hi@docqai.com)
    #     """
    # )

    # handle_fire_extensions_callbacks("webui.home_page.render_footer", None)

    # with login_container:
    #     auth_required(show_login_form=True, requiring_selected_org_admin=False, show_logout_button=True)
