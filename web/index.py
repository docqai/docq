"""Page: Home (no auth required)."""

import streamlit as st
from docq import setup
from st_pages import Page, Section, add_page_title, show_pages
from utils.layout import auth_required, production_layout

setup.init()

production_layout()

add_page_title()

show_pages(
    [
        Page("web/index.py", "Home", "🏠"),
        Section("Your_Space", icon="📁"),
        Page("web/personal_chat.py", "General_Chat"),
        Page("web/personal_ask.py", "Ask_Your_Documents"),
        Page("web/personal_docs.py", "Manage_Your_Documents"),
        Section("Shared_Spaces", icon="💼"),
        Page("web/shared_ask.py", "Ask_Shared_Documents"),
        Section("Admin", icon="💂"),
        Page("web/admin_overview.py", "Admin_Overview"),
        Page("web/admin_users.py", "Admin_Users"),
        Page("web/admin_docs.py", "Admin_Docs"),
        Page("web/admin_logs.py", "Admin_Logs"),
    ]
)

auth_required()

st.subheader("Welcome to Docq - Private & Secure AI Knowledge Insight")

st.markdown(
    """
- Click on the _General Chat_ link to use Docq like ChatGPT.
- Click on the _Ask Your Documents_ link to ask questions and get answers from your own documents. You can also _Manage Your Documents_.
- Click on the _Ask Shared Documents_ link to ask questions and get answers from documents shared within your organisation.
"""
)

st.subheader("Tips & Tricks")
st.markdown(
    """
- Always ask questions in plane English and try to be as specific as possible.
- You can manage the documents in your space which sets the context for your questions.
- Your access to shared spaces is subject to permissions set by your organisation.
- For any questions or feedback, please contact your organisation's Docq administrator.
"""
)

st.markdown("Enjoy [Docq](https://docq.ai)!")
