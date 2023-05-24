import streamlit as st
from st_pages import Page, Section, add_page_title, show_pages
from docq import setup

setup.init()

add_page_title()

show_pages(
    [
        Page("web/index.py", "Home", "🏠"),
        Page("web/admin/index.py", "Admin", "💂"),
        Section("Personal", icon="📁"),
        Page("web/personal/index.py", "Your Space"),
        Section("Org-wide", icon="💼"),
        Page("web/shared/index.py", "Shared Spaces"),
    ]
)

st.subheader("Welcome to Docq - Private & Secure AI Knowledge Insight")

st.markdown("""
- Click on the **Your Space** link to ask questions and get answers from your own documents.
- Click on the **Shared Spaces** link to ask questions and get answers from documents in your organisation.
""")

st.subheader("Tips & Tricks")
st.markdown("""
- Always ask questions in plane English and try to be as specific as possible.
- You can manage the documents in your space which sets the context for your questions.
- Your access to shared spaces is subject to permissions set by your organisation.
- For any questions or feedback, please contact your organisation's Docq administrator.
""")

st.markdown("Enjoy [Docq](https://docq.ai)!")
