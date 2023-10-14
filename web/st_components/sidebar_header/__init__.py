"""Nav UI example."""
import base64
import json
import os
from datetime import datetime
from typing import Self
from urllib.parse import unquote

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
    __auth_state: str = "unauthenticated"
    __active_elements: list = [
        "docq-org-dropdown",
        "docq-header-container",
        "docq-floating-action-button",
    ]

    def __init__(self: Self,) -> None:
        """Initialize the class."""
        self.__header_style = load_file_variables(css_path, {})
        self._load_script()

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
    def org_options_list(self: Self,) -> str:
        """Get the json string containing available orgs."""
        return self.__org_options_json

    @org_options_list.setter
    def org_options_list(self: Self, value: list) -> None:
        """Set the json string containing available orgs."""
        self.__org_options_json = json.dumps(value)
        self._load_script()

    @property
    def logo_url(self: Self,) -> str:
        """Get the URL to logo."""
        return self.__logo_url

    @property
    def active_elements(self: Self,) -> list:
        """Get the active elements."""
        return json.dumps(self.__active_elements)

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

    @property
    def auth_state(self: Self,) -> str:
        """Get the auth state."""
        return self.__auth_state

    @auth_state.setter
    def auth_state(self: Self, value: bool) -> None:
        """Set the auth state."""
        auth_state = "authenticated" if value else "unauthenticated"
        if auth_state == "unauthenticated" and self.__auth_state != auth_state:
            self.reset_user_details()
        self.__auth_state = auth_state
        self._load_script()

    def reset_user_details(self: Self,) -> None:
        """Reset the instance."""
        self.__selected_org = None
        self.__org_options_json = None
        self.__auth_state = "unauthenticated"

    def _load_script(self: Self,) -> None:
        params = {
            "selected_org": self.selected_org,
            "org_options_json": self.org_options_list,
            "logo_url": self.logo_url,
            "style_doc": self.style,
            "auth_state": self.auth_state,
        }
        self.__header_script = load_file_variables(script_path, params)


__side_bar_header_api = _SideBarHeaderAPI()


def _setup_page_script(auth_state: bool) -> None:
    """Setup the page script."""
    __side_bar_header_api.auth_state = auth_state


def set_selected_org(selected_org: str) -> None:
    """Set the current org."""
    __side_bar_header_api.selected_org = selected_org


def update_org_options(org_options: list) -> None:
    """Update the org options."""
    __side_bar_header_api.org_options_list = org_options


def get_selected_org_from_ui() -> str | None:
    """Get the current org."""
    param = st.experimental_get_query_params().get("org", [None])[0]
    if param is not None:
        org, timestamp = base64.b64decode(
            unquote(param)
        ).decode("utf-8").split("::")
        now_ = datetime.now()
        if now_.timestamp() - float(timestamp) < 60:
            return org
    return None


def _run_script(auth_state: bool, selected_org: str = None, org_options: list = None) -> None:
    """Run the script."""
    __side_bar_header_api.selected_org = selected_org
    __side_bar_header_api.org_options_list = org_options
    __side_bar_header_api.auth_state = auth_state
    components.html(f"""
        // ST-SIDEBAR-SCRIPT-CONTAINER
        <script>{__side_bar_header_api.script}</script>
        """,
        height=0
    )


def _cleanup_script() -> None:
    """Cleanup the script."""
    __side_bar_header_api.reset_user_details()
    components.html(f"""
        <script>
            const active_elements = `{__side_bar_header_api.active_elements}`;
            JSON.parse(active_elements).forEach(id => {{
                const element = window.parent.document.getElementById(id);
                if (element) element.remove();
            }});
        </script>
        """,
        height=0
    )



run_script = _run_script
