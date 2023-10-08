"""Nav UI example."""
import json
import os
from typing import Self

import streamlit as st
import streamlit.components.v1 as components

from ..static_utils import load_file_variables

parent_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(parent_dir, "static", "sidebar.js")
css_path = os.path.join(parent_dir, "static", "sidebar.css")

class _SideBarHeaderAPI:
    """Custom API for the st_components package."""

    __selected_org: str = None
    __org_options_json: str = None
    __logo_url: str = None
    __header_script: str = None
    __header_style: str = None

    def __init__(self: Self,) -> None:
        """Initialize the class."""
        self._load_script()
        self._load_style()

    @property
    def selected_org(self: Self,) -> str:
        """Get the currently selected org."""
        return self.__selected_org

    @selected_org.setter
    def selected_org(self: Self, value: str) -> None:
        """Set the currently selected org."""
        self.__selected_org = value
        self._load_script()

    @property
    def org_options_json(self: Self,) -> str:
        """Get the json string containing available orgs."""
        return self.__org_options_json

    @org_options_json.setter
    def org_options_json(self: Self, value: dict) -> None:
        """Set the json string containing available orgs."""
        self.__org_options_json = json.dumps(value)
        self._load_script()

    @property
    def logo_url(self: Self,) -> str:
        """Get the URL to logo."""
        return self.__logo_url

    @logo_url.setter
    def logo_url(self: Self, value: str) -> None:
        """Set the URL to logo."""
        self.__logo_url = value
        self._load_script()

    @property
    def script(self: Self,) -> str:
        """Get the script."""
        return self.__header_script

    @property
    def style(self: Self,) -> str:
        """Get the style."""
        return self.__header_style

    def _load_script(self: Self,) -> None:
        params = {
            "selected_org": self.selected_org,
            "org_options_json": self.org_options_json,
            "logo_url": self.logo_url,
        }
        self.__header_script = load_file_variables(script_path, params)

    def _load_style(self: Self,) -> None:
        params = {}
        self.__header_style = load_file_variables(css_path, params)


__side_bar_header_api = _SideBarHeaderAPI()


def render_sidebar(selected_org: str, org_options: list, logo_url: str = None) -> None:
    """Docq sidebar header component.

    Args:
        selected_org: The currently selected org.
        org_options: json string containing available orgs.
        logo_url: URL to logo.
    """
    __side_bar_header_api.selected_org = selected_org
    __side_bar_header_api.org_options_json = org_options
    __side_bar_header_api.logo_url = logo_url
    st.markdown(f"<style>{__side_bar_header_api.style}</style>", unsafe_allow_html=True)
    components.html(f"""
        // ST-SIDEBAR-SCRIPT-CONTAINER
        <script>{__side_bar_header_api.script}</script>
        """,
        height=0
    )


def set_selected_org(selected_org: str) -> None:
    """Set the current org."""
    __side_bar_header_api.selected_org = selected_org


def update_org_options(org_options: list) -> None:
    """Update the org options."""
    __side_bar_header_api.org_options_json = org_options


def get_selected_org() -> str:
    """Get the current org."""
    return st.experimental_get_query_params().get("org", [None])[0]
