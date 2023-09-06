#!/usr/bin/env -S streamlit run --server.port 8502
"""Simple Streamlit app to demo embedding of Docq in an iframe."""
import streamlit as st
from docq.config import FeatureType
from docq.domain import FeatureKey
from docq.embed_config import web_embed_config
from utils.layout import auth_required, chat_ui, feature_enabled
from utils.sessions import get_authenticated_user_id

auth_required(show_login_form=False, show_logout_button=False)

st.session_state["no_auth"] = True

feature_enabled(FeatureType.ASK_SHARED)

web_embed_config()

feature = FeatureKey(FeatureType.ASK_SHARED, get_authenticated_user_id())

chat_ui(feature)
