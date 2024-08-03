"""Page: Home (no auth required)."""

import streamlit as st

# from docq_extensions.web.layout import subscriptions
from utils.handlers import (
    handle_fire_extensions_callbacks,  # noqa F401 don't remove this line, it's used to register api routes
)
from utils.layout import (
    auth_required,
    public_access,
    render_docq_logo,
    render_page_title_and_favicon,
)
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("home_page", attributes=baggage_as_attributes()):
    render_docq_logo()

    render_page_title_and_favicon(
        page_display_title=":violet[Your private ChatGPT alternative].",
        browser_title="Docq.AI - Private ChatGPT alternative.",
    )

    public_access()

    login_container = st.container()

    st.subheader("Secure unlock knowledge from your confidential business documents.")

    st.markdown("Upload a document. Ask questions. Get answers. It's that simple!")

    st.subheader("Guide")
    st.markdown(
        """
    - **_General Chat_** to use Docq like ChatGPT.
    - **_Ask Shared Documents_** to ask questions and get answers from documents shared within your organisation as a Space.
    - **_Admin Section_ > _Admin Spaces_** to create a new Space, add documents, and share with your organisation.
    """
    )

    st.subheader("Tips & Tricks")
    st.markdown(
        """
    - Always ask questions in plain English and try to be as specific as possible.
    - Admins can manage the documents in a Space which sets the context for your questions.
    - Every user also has a personal organisation so you can create Spaces that are personal knowledge repositories.
    - Your access to shared spaces is subject to permissions set by your organisation admin.
    - For any questions or feedback, please contact your organisation's Docq administrator.

    Enjoy Docq!
    """
    )

    st.divider()
    st.markdown(
        """
    [Website](https://docq.ai) | Star on [Github](https://github.com/docqai) | Follow on [Twitter](https://twitter.com/docqai)
        """
    )

    st.markdown(
        """
    For help: [Docs](https://docqai.github.io/docq/) | Join [Slack](https://join.slack.com/t/docqai/shared_invite/zt-27p17lu6v-6KLJxSmt61vfNqCavSE73A) | Email [hi@docqai.com](mailto:hi@docqai.com)
        """
    )

    handle_fire_extensions_callbacks("webui.home_page.render_footer", None)

    with login_container:
        auth_required(show_login_form=True, requiring_selected_org_admin=False, show_logout_button=True)
