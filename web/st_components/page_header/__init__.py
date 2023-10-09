"""Header bar."""
import json
import os
from contextlib import contextmanager
from typing import Self

import streamlit as st
from streamlit.components.v1 import html

from ..static_utils import load_file_variables

parent_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(parent_dir, "static", "header.js")
css_path = os.path.join(parent_dir, "static", "header.css")


class _PageHeaderAPI:
    """Page header bar API."""

    __menu_options_json: str = None
    __menu_options_list: list = [] # [{"text": "Home", "key": "home"}]
    __username: str = None
    __avatar_src: str = None
    __page_script: str = None
    __page_style: str = None

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
                return
        self.__menu_options_list.append({"text": label, "key": key})
        self.__menu_options_json = json.dumps(self.__menu_options_list)
        self._load_script()

    def _load_script(self: Self,) -> None:
        """Load the script."""
        script_args = {
            "username": self.__username,
            "avatar_src": self.__avatar_src,
            "menu_items_json": self.__menu_options_json,
            "style_doc": self.__page_style,
        }
        self.__page_script = load_file_variables(script_path, script_args)


__page_header_api = _PageHeaderAPI()

def render_header(username: str, avatar_src: str) -> None:
    """Header bar.

    Args:
        username (str): Username.
        avatar_src (str): Avatar source.
    """
    __page_header_api.username = username
    __page_header_api.avatar_src = avatar_src
    html(f"<script>{__page_header_api.script}</script>",height=0,)


@contextmanager
def menu_option(label: str, key: str = None) -> None:
    """Add a menu option."""
    f_label = label.strip().replace(" ", "_").lower()
    __button_key = st.button(label=f_label, key=key, type="primary")
    __page_header_api.add_menu_option(label=label, key=f_label)
    yield __button_key
