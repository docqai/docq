"""Page: Home (no auth required)."""

import socket

import streamlit as st
from utils.handlers import (
    handle_fire_extensions_callbacks,  # noqa F401 don't remove this line, it's used to register api routes
)

# from docq_extensions.web.layout import subscriptions
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
        page_display_title=":violet[Your private ChatGPT].",
        browser_title="Docq.AI - Private ChatGPT/Perplexity.",
    )

    public_access()

    login_container = st.container()

    st.subheader("Securely unlock knowledge from your confidential business documents using GenAI.")

    st.markdown("Upload a document. Ask questions. Get answers. It's that simple!")

    st.subheader("Quick Start")
    st.markdown(
        """
    - **_General Chat_** to use Docq like ChatGPT.
    - **_Ask Shared Documents_**
        - Select a Space > ask questions and get answers.
        - Upload an adhoc doc to a thread and ask questions.
    - **_Admin Section_ > _Admin Spaces_** to create a new Space, add documents, and share with your organisation.
    """
    )

    hostname = socket.gethostname()
    st.subheader("Use Cases")
    st.markdown(
        f"""
        Here are some use cases where traditionally there are inter-team/person dependencies that **slows down progress** of work. Docq can **reduce these dependencies** therefore speed things up.

    - Company Lingo Explainer
    - New Employee Mentor
    - Sales Pitch Assistant
    - Product Marketing Assistant
    - Platform Engineering Support Bot
    - Internal IT Support Bot

    For more details on **how**, see our [website](https://docq.ai/?utm_source={hostname}&utm_medium=web&utm_campaign=product#usecases) and this [blog post](https://medium.com/@docqai/six-genai-use-cases-that-will-increase-efficiency-and-productivity-in-your-business-71137ce0a270)."""
    )

    st.subheader("Features - powered by GenAI")
    st.markdown(
        """
    - Chat with your private documents - Ask questions and get answers.
    - Spaces to organise documents - Admins create shared Spaces with documents and set permissions.
    - Personal organisation - for every user so you can create Spaces that are personal knowledge repositories.
    - Adhoc document upload for quick questions and answers - any user can start a new thread an upload docs to the thread.
    - Chrome Extension - for quick in context access in a browser side panel (page context features coming soon).
    - Slack Integration - for setting up workflows that are in Slack like team support bots in the support channel.
    - Private AI Models (LLMs) - serverless from AWS/Azure/GCP/Groq to dedicated deployments.

    Enjoy Docq!
    """
    )

    st.divider()
    st.markdown(
        """
        Drop us a line if you have any questions or feedback. We'd love to hear from you!

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
