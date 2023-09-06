#!/usr/bin/env -S streamlit run --server.port 8502
"""Simple Streamlit app to demo embedding of Docq in an iframe."""

from docq.config import FeatureType
from docq.domain import FeatureKey
from docq.embed_config import web_embed_config
from utils.layout import chat_ui, feature_enabled

feature_enabled(FeatureType.ASK_PUBLIC)


web_embed_config()

feature = FeatureKey(FeatureType.ASK_PUBLIC, 1)

chat_ui(feature)
