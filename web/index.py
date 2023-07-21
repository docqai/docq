"""Page: Home (no auth required)."""

import streamlit as st
from docq import setup
from st_pages import Page, Section, add_page_title, show_pages
from utils.layout import production_layout, public_access

setup.init()

production_layout()

show_pages(
    [
        Page("web/index.py", "Home", "🏠"),
        Section("Your_Space", icon="📁"),
        Page("web/personal_chat.py", "General_Chat"),
        Page("web/personal_ask.py", "Ask_Your_Documents"),
        Page("web/personal_docs.py", "Manage_Your_Documents"),
        Section("Shared_Spaces", icon="💼"),
        Page("web/shared_ask.py", "Ask_Shared_Documents"),
        Page("web/shared_spaces.py", "List_Shared_Spaces"),
        Section("Admin", icon="💂"),
        Page("web/admin_settings.py", "Admin_Settings"),
        Page("web/admin_spaces.py", "Admin_Spaces"),
        Page("web/admin_space_groups.py", "Admin_Space_Groups"),
        Page("web/admin_docs.py", "Admin_Docs"),
        Page("web/admin_users.py", "Admin_Users"),
        Page("web/admin_user_groups.py", "Admin_User_Groups"),
        Page("web/admin_logs.py", "Admin_Logs"),
    ]
)

public_access()

add_page_title()

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
