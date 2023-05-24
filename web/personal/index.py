import streamlit as st
from st_pages import add_page_title

from web.constants import SpaceType
from web.layout import chat_ui, documents_ui
from web.utils import init


type_ = SpaceType.PERSONAL

init(type_)

add_page_title()

tab_chat, tab_manage = st.tabs(["Ask Questions", "Manage Documents"])


with tab_chat:
    st.subheader("Ask")

    chat_ui(type_)

with tab_manage:
    st.subheader("Manage")

    documents_ui(type_)