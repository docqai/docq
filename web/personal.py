"""Page: Personal / Ask Your Documents."""

import streamlit as st
from docq.config import FeatureType, SpaceType
from docq.domain import FeatureKey, SpaceKey
from st_pages import add_page_title
from utils.handlers import get_authenticated_user_id
from utils.layout import auth_required, chat_ui, documents_ui

add_page_title()

auth_required()

feature = FeatureKey(FeatureType.ASK_PERSONAL, get_authenticated_user_id())
space = SpaceKey(SpaceType.PERSONAL, get_authenticated_user_id())

tab_ask, tab_documents = st.tabs(["Ask Questions", "Manage Documents"])

with tab_ask:
    st.subheader("Ask")
    chat_ui(feature)

with tab_documents:
    st.subheader("Documents")
    documents_ui(space)
