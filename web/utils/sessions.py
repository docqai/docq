"""Session utilities."""

from typing import Any

import streamlit as st
from docq import config, manage_users

from .constants import (
    SESSION_KEY_NAME_DOCQ,
    SessionKeyNameForAuth,
    SessionKeyNameForChat,
    SessionKeyNameForPublic,
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


def reset_session_state() -> None:
    """Reset the session state. This must be called for user login and logout."""
    st.session_state[SESSION_KEY_NAME_DOCQ] = {}


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


def is_current_user_super_admin() -> bool:
    """Get the auth session value for SUPER_ADMIN."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.SUPER_ADMIN.name)


def is_current_user_selected_org_admin() -> bool:
    """Get the auth session value for SELECTED_ORG_ADMIN."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.SELECTED_ORG_ADMIN.name)


def set_if_current_user_is_selected_org_admin(selected_org_id: int) -> None:
    """Check if the current user is org_admin of the selected org. Then set SELECTED_ORG_ADMIN session to True or False."""
    is_org_admin = False
    current_user_id = get_authenticated_user_id()
    org_admins = manage_users.list_users_by_org(org_id=selected_org_id, org_admin_match=True)
    is_org_admin = current_user_id in [x[0] for x in org_admins]
    _set_session_value(is_org_admin, SessionKeySubName.AUTH, SessionKeyNameForAuth.SELECTED_ORG_ADMIN.name)


def set_auth_session(val: dict = None) -> None:
    """Set the auth session value."""
    _set_session_value(val, SessionKeySubName.AUTH)


def get_authenticated_user_id() -> int | None:
    """Get the authenticated user id."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.ID.name)


def get_selected_org_id() -> int | None:
    """Get the selected org_id context."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.SELECTED_ORG_ID.name)


def set_selected_org_id(org_id: int) -> None:
    """Set the selected org_id context."""
    _set_session_value(org_id, SessionKeySubName.AUTH, SessionKeyNameForAuth.SELECTED_ORG_ID.name)


def get_username() -> str | None:
    """Get the authenticated user name."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.USERNAME.name)


def get_settings_session(key: SessionKeyNameForSettings = None) -> dict | None:
    """Get the settings session value."""
    return _get_session_value(SessionKeySubName.SETTINGS, key.name if key is not None else None)


def set_settings_session(val: dict = None, key: SessionKeyNameForSettings = None) -> None:
    """Set the settings session value."""
    _set_session_value(val, SessionKeySubName.SETTINGS, key.name if key is not None else None)


def set_public_session(val: dict = None, key: SessionKeyNameForPublic = None) -> None:
    """Set the public session value."""
    _set_session_value(val, SessionKeySubName.PUBLIC, key.name if key is not None else None)


def get_public_session(key: SessionKeyNameForPublic = None) -> dict | None:
    """Get the public session value."""
    return _get_session_value(SessionKeySubName.PUBLIC, key.name if key is not None else None)


def get_active_public_session() -> str | None:
    """Get the public session id."""
    return _get_session_value(SessionKeySubName.PUBLIC, SessionKeyNameForPublic.SESSION.name)
