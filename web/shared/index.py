import streamlit as st
from st_pages import add_page_title

from web.constants import SpaceType
from web.layout import chat_ui, spaces_ui
from web.utils import init


type_ = SpaceType.SHARED

init(type_)

add_page_title()


tab_chat, tab_manage = st.tabs(["Ask Questions", "List Available Spaces"])


with tab_chat:
    st.subheader("Ask")

    chat_ui(type_)


with tab_manage:
    st.subheader("List")

    spaces_ui(type_)
