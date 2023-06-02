"""Page: Personal / General Chat."""

import streamlit as st
from docq.config import FeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.handlers import get_authenticated_user_id
from utils.layout import auth_required, chat_settings_ui, chat_ui

add_page_title()

auth_required()

feature = FeatureKey(FeatureType.CHAT_PRIVATE, get_authenticated_user_id())

tab_chat, tab_settings = st.tabs(["General Chat", "Chat Settings"])

with tab_chat:
    st.subheader("Chat")
    chat_ui(feature)

with tab_settings:
    st.subheader("Settings")
    chat_settings_ui(feature)
