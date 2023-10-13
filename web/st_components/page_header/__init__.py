"""Header bar."""
import json
import logging as log
import os
from typing import Self

import streamlit as st
from streamlit.components.v1 import html

from ..static_utils import get_current_page_info, load_file_variables

parent_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(parent_dir, "static", "header.js")
css_path = os.path.join(parent_dir, "static", "header.css")

api_key = "page_header_api{page_script_hash}_{page_name}"


class _PageHeaderAPI:
    """Page header bar API."""

    __menu_options_json: str = None
    __menu_options_list: list = [] # [{"text": "Home", "key": "home"}]
    __username: str = None
    __avatar_src: str = None
    __page_script: str = None
    __page_style: str = None
    __fab_config: str = None
    __auth_state: str = None

    def __init__(self: Self,) -> None:
        """Initialize the class."""
        self.__page_style = load_file_variables(css_path, {})
        self._load_script()

    @property
    def menu_options_json(self: Self,) -> str:
        """Get the json string containing available menu options."""
        return self.__menu_options_json

    @property
    def menu_options_list(self: Self,) -> dict:
        """Get the dict containing available menu options."""
        return self.__menu_options_list

    @property
    def username(self: Self,) -> str:
        """Get the username."""
        return self.__username

    @property
    def avatar_src(self: Self,) -> str:
        """Get the avatar source."""
        return self.__avatar_src

    @property
    def script(self: Self,) -> str:
        """Get the script."""
        return self.__page_script

    @property
    def auth_state(self: Self,) -> str:
        """Get the auth state."""
        return self.__auth_state

    @auth_state.setter
    def auth_state(self: Self, value: bool) -> None:
        """Set the auth state."""
        if value:
            self.__auth_state = "authenticated"
        else:
            self.__auth_state = "unauthenticated"
        self._load_script()

    @menu_options_list.setter
    def menu_options_list(self: Self, value: list) -> None:
        """Set the dict containing available menu options."""
        self.__menu_options_list = value
        self.__menu_options_json = json.dumps(value)
        self._load_script()

    @username.setter
    def username(self: Self, value: str) -> None:
        """Set the username."""
        self.__username = value
        self._load_script()

    @avatar_src.setter
    def avatar_src(self: Self, value: str) -> None:
        """Set the avatar source."""
        self.__avatar_src = value
        self._load_script()

    def add_menu_option(self: Self, label: str, key: str, icon_html_: str = None) -> None:
        """Add a menu option."""
        for entry in self.__menu_options_list:
            if entry["text"] == label and entry["key"] == key:
                self.__menu_options_json = json.dumps(self.__menu_options_list)
                self._load_script()
                return
        self.__menu_options_list.append({"text": label, "key": key})
        self.__menu_options_json = json.dumps(self.__menu_options_list)
        self._load_script()

    def setup_fab(self: Self, tool_tip_label: str, key: str, icon: str = "+") -> None:
        """Setup floating action button."""
        self.__fab_config = json.dumps({"label": tool_tip_label, "key": key, "icon": icon})
        self._load_script()

    def _load_script(self: Self,) -> None:
        """Load the script."""
        script_args = {
            "username": self.__username,
            "avatar_src": self.__avatar_src,
            "menu_items_json": self.__menu_options_json,
            "style_doc": self.__page_style,
            "fab_config": self.__fab_config,
            "auth_state": self.__auth_state,
        }
        self.__page_script = load_file_variables(script_path, script_args)


# Run this at the start of each page
def _setup_page_script(auth_state: bool) -> None:
    """Setup page script."""
    script_caller_info = get_current_page_info()
    try:
        _key = api_key.format(
            page_script_hash=script_caller_info["page_script_hash"],
            page_name=script_caller_info["page_name"]
            )
        __page_header_api = _PageHeaderAPI()
        __page_header_api.auth_state = auth_state
        st.session_state[_key] = __page_header_api
        # html(f"<script>{__page_header_api.script}</script>",height=0,)
    except Exception as e:
        log.error("Page header not initialized properly. error: %s", e)


def _menu_option(label: str, key: str = None) -> bool:
    """Add a menu option."""
    f_label = label.strip().replace(" ", "_").lower()
    script_caller_info = get_current_page_info()
    try:
        _key = api_key.format(
            page_script_hash=script_caller_info["page_script_hash"],
            page_name=script_caller_info["page_name"]
            )
        __page_header_api: _PageHeaderAPI = st.session_state[_key]
        __page_header_api.add_menu_option(label=label, key=f_label)
        return st.button(label=f_label, key=key, type="primary")
    except KeyError as e:
        log.error("Page header not initialized. Please run `setup_page_script` first. error: %s", e)


def _floating_action_button(label: str, key: str = None, icon: str = None) -> bool:
    """Add a floating action button."""
    f_label = label.strip().replace(" ", "_").lower()
    script_caller_info = get_current_page_info()
    try:
        _key = api_key.format(
            page_script_hash=script_caller_info["page_script_hash"],
            page_name=script_caller_info["page_name"]
            )
        __page_header_api: _PageHeaderAPI = st.session_state[_key]
        __page_header_api.setup_fab(tool_tip_label=label, key=f_label, icon=icon)
        return st.button(label=f_label, key=key, type="primary")
    except KeyError as e:
        log.error("Page header not initialized. Please run `setup_page_script` first. error: %s", e)


def _run_script(auth_state: bool, username: str = None, avatar_src: str = None) -> None:
    """Render the header bar.

    Args:
        auth_state (bool): Authentication state.
        username (str): Username.
        avatar_src (str): Avatar source.
    """
    script_caller_info = get_current_page_info()
    try:
        _key = api_key.format(
            page_script_hash=script_caller_info["page_script_hash"],
            page_name=script_caller_info["page_name"]
        )
        __page_header_api: _PageHeaderAPI = st.session_state[_key]
        __page_header_api.auth_state = auth_state
        __page_header_api.username = username
        __page_header_api.avatar_src = avatar_src
        html(f"<script>{__page_header_api.script}</script>",height=0,)
    except KeyError as e:
        log.error("Page header not initialized. Please run `setup_page_script` first. error: %s", e)


floating_action_button = _floating_action_button
menu_option = _menu_option
run_script = _run_script
