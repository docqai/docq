"""Page: Shared / Ask Shared Documents."""

import streamlit as st
from docq.config import FeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.layout import auth_required, chat_ui, feature_enabled, list_spaces_ui
from utils.sessions import get_authenticated_user_id

auth_required()

feature_enabled(FeatureType.ASK_SHARED)

add_page_title()

feature = FeatureKey(FeatureType.ASK_SHARED, get_authenticated_user_id())

tab_ask, tab_spaces = st.tabs(["Ask Questions", "List Available Spaces"])

with tab_ask:
    st.subheader("Ask")
    chat_ui(feature)

with tab_spaces:
    st.subheader("List")
    list_spaces_ui()
