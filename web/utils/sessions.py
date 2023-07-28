"""Session utilities."""

from typing import Any

import streamlit as st
from docq import config

from .constants import (
    SESSION_KEY_NAME_DOCQ,
    SessionKeyNameForAuth,
    SessionKeyNameForChat,
    SessionKeyNameForSettings,
    SessionKeySubName,
)


def _init_session_state() -> None:
    if SESSION_KEY_NAME_DOCQ not in st.session_state:
        st.session_state[SESSION_KEY_NAME_DOCQ] = {}
    for n in SessionKeySubName:
        if n.name not in st.session_state[SESSION_KEY_NAME_DOCQ]:
            st.session_state[SESSION_KEY_NAME_DOCQ][n.name] = {}
    for n in config.FeatureType:
        if n.name not in st.session_state[SESSION_KEY_NAME_DOCQ][SessionKeySubName.CHAT.name]:
            st.session_state[SESSION_KEY_NAME_DOCQ][SessionKeySubName.CHAT.name][n.name] = {}


def _get_session_value(name: SessionKeySubName, key_: str = None, subkey_: str = None) -> Any | None:
    _init_session_state()
    val = st.session_state[SESSION_KEY_NAME_DOCQ][name.name]
    if key_ is None and subkey_ is None:
        return val
    elif subkey_ is None:
        return val[key_]
    else:
        return val[key_][subkey_]


def _set_session_value(val: Any | None, name: SessionKeySubName, key: str = None, subkey: str = None) -> None:
    _init_session_state()
    if key is None and subkey is None:
        st.session_state[SESSION_KEY_NAME_DOCQ][name.name] = val
    elif subkey is None:
        st.session_state[SESSION_KEY_NAME_DOCQ][name.name][key] = val
    else:
        st.session_state[SESSION_KEY_NAME_DOCQ][name.name][key][subkey] = val


def get_chat_session(type_: config.FeatureType = None, key_: SessionKeyNameForChat = None) -> Any | None:
    """Get the chat session value."""
    _init_session_state()
    return _get_session_value(
        SessionKeySubName.CHAT,
        type_.name if type_ is not None else None,
        key_.name if key_ is not None else None,
    )


def set_chat_session(val: Any | None, type_: config.FeatureType = None, key_: SessionKeyNameForChat = None) -> None:
    """Set the chat session value."""
    _init_session_state()
    _set_session_value(
        val,
        SessionKeySubName.CHAT,
        type_.name if type_ is not None else None,
        key_.name if key_ is not None else None,
    )


def get_auth_session() -> dict:
    """Get the auth session value."""
    return _get_session_value(SessionKeySubName.AUTH)


def set_auth_session(val: dict = None) -> None:
    """Set the auth session value."""
    _set_session_value(val, SessionKeySubName.AUTH)


def get_authenticated_user_id() -> int | None:
    """Get the authenticated user id."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.ID.name)


def get_settings_session(key: SessionKeyNameForSettings = None) -> dict | None:
    """Get the settings session value."""
    return _get_session_value(SessionKeySubName.SETTINGS, key.name if key is not None else None)


def set_settings_session(val: dict = None, key: SessionKeyNameForSettings = None) -> None:
    """Set the settings session value."""
    _set_session_value(val, SessionKeySubName.SETTINGS, key.name if key is not None else None)
