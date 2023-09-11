"""Configuration for web embed."""

import streamlit as st
from st_pages import hide_pages

hide_sidebar_style = """
<style>
    [data-testid="collapsedControl"] {
        display: none !important;
    }

    section[data-testid="stSidebar"] {
        display: none !important;
    }

    .block-container {
        padding-top: 1rem !important;
    }

    .stChatFloatingInputContainer {
        padding-bottom: 3rem !important;
    }

    div.element-container:has(.stAlert) {
        padding-top: 2rem !important;
    }

    </style>
"""

def _web_embed_config() -> None:
    st.markdown(hide_sidebar_style, unsafe_allow_html=True)

def _root_embed_config() -> None:
    hide_pages(["widget"])

def web_embed_config() -> None:
    """Configuration for web embed."""
    _web_embed_config()

def root_embed_config() -> None:
    """Root configuration for the web widget page."""
    _root_embed_config()