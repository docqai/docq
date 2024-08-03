"""Session utilities."""

import logging
from typing import Any, Optional

import docq
import streamlit as st
from docq import config, manage_users
from docq.support.auth_utils import set_cache_auth_session
from opentelemetry import trace

from .constants import (
    SESSION_KEY_NAME_DOCQ,
    SessionKeyNameForAuth,
    SessionKeyNameForChat,
    SessionKeyNameForSettings,
    SessionKeySubName,
)

tracer = trace.get_tracer(__name__, docq.__version_str__)


def _init_session_state() -> None:
    if SESSION_KEY_NAME_DOCQ not in st.session_state:
        st.session_state[SESSION_KEY_NAME_DOCQ] = {}
    for n in SessionKeySubName:
        if n.name not in st.session_state[SESSION_KEY_NAME_DOCQ]:
            st.session_state[SESSION_KEY_NAME_DOCQ][n.name] = {}
    for n in config.OrganisationFeatureType:
        if n.name not in st.session_state[SESSION_KEY_NAME_DOCQ][SessionKeySubName.CHAT.name]:
            st.session_state[SESSION_KEY_NAME_DOCQ][SessionKeySubName.CHAT.name][n.name] = {}

@tracer.start_as_current_span("session_state_exists")
def session_state_exists() -> bool:
    """Check if any session state exists."""
    return SESSION_KEY_NAME_DOCQ in st.session_state


def reset_session_state() -> None:
    """Reset the session state. This must be called for user login and logout."""
    st.session_state[SESSION_KEY_NAME_DOCQ] = {}
    logging.debug("called reset_session_state()")


def _get_session_value(name: SessionKeySubName, key_: Optional[str] = None, subkey_: Optional[str] = None) -> Any | None:
    _init_session_state()
    val = st.session_state[SESSION_KEY_NAME_DOCQ][name.name]
    if key_ is None and subkey_ is None:
        return val
    elif subkey_ is None and key_ in val:
        return val[key_]
    elif key_ in val and subkey_ in val[key_]:
        return val[key_][subkey_]
    else:
        return None


def _set_session_value(val: Any | None, name: SessionKeySubName, key: Optional[str] = None, subkey: Optional[str] = None) -> None:
    _init_session_state()
    if key is None and subkey is None:
        st.session_state[SESSION_KEY_NAME_DOCQ][name.name] = val
    elif subkey is None:
        st.session_state[SESSION_KEY_NAME_DOCQ][name.name][key] = val
    else:
        st.session_state[SESSION_KEY_NAME_DOCQ][name.name][key][subkey] = val


def get_chat_session(type_: Optional[config.OrganisationFeatureType] = None, key_: Optional[SessionKeyNameForChat] = None) -> Any | None:
    """Get the chat session value."""
    _init_session_state()
    return _get_session_value(
        SessionKeySubName.CHAT,
        type_.name if type_ is not None else None,
        key_.name if key_ is not None else None,
    )


def set_chat_session(val: Any | None, type_: Optional[config.OrganisationFeatureType] = None, key_: Optional[SessionKeyNameForChat] = None) -> None:
    """Set the chat session value."""
    _init_session_state()
    _set_session_value(
        val,
        SessionKeySubName.CHAT,
        type_.name if type_ is not None else None,
        key_.name if key_ is not None else None,
    )


def set_auth_session(val: Optional[dict] = None, cache: bool = False) -> None:
    """Set the auth session value."""
    _set_session_value(val, SessionKeySubName.AUTH)
    if cache:
        # this persists the auth session across browser session in Streamlit i.e. when the user hits refresh.
        set_cache_auth_session(val)

@tracer.start_as_current_span("get_auth_session")
def get_auth_session() -> dict:
    """Get the auth session value."""
    return _get_session_value(SessionKeySubName.AUTH)


def is_current_user_authenticated() -> bool:
    """Return if the current user is authenticated or not."""
    return bool(get_auth_session())


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


def get_authenticated_user_id() -> int | None:
    """Get the authenticated user id."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.ID.name)


def get_selected_org_id() -> int | None:
    """Get the selected org_id context."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.SELECTED_ORG_ID.name)


def set_selected_org_id(org_id: int) -> None:
    """Set the selected org_id context."""
    _set_session_value(org_id, SessionKeySubName.AUTH, SessionKeyNameForAuth.SELECTED_ORG_ID.name)

def set_selected_assistant(assistant_scoped_id: str) -> None:
    """Set the selected person key in session settings."""
    _set_session_value(
        assistant_scoped_id, SessionKeySubName.SETTINGS, SessionKeyNameForSettings.USER.name, "assistant_scoped_id"
    )


def get_selected_assistant() -> str | None:
    """Get the selected person key from session settings.

    Returns:
        str | None: The selected assistant scoped id which is unique across tables.
    """
    assistant_scoped_id = _get_session_value(
        SessionKeySubName.SETTINGS, SessionKeyNameForSettings.USER.name, "assistant_scoped_id"
    )
    return assistant_scoped_id


def get_username() -> str | None:
    """Get the authenticated user name."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.USERNAME.name)


def get_settings_session(key: Optional[SessionKeyNameForSettings] = None) -> dict | None:
    """Get the settings session value."""
    return _get_session_value(SessionKeySubName.SETTINGS, key.name if key is not None else None)


def set_settings_session(val: Optional[dict] = None, key: Optional[SessionKeyNameForSettings] = None) -> None:
    """Set the settings session value."""
    _set_session_value(val, SessionKeySubName.SETTINGS, key.name if key is not None else None)


def get_public_space_group_id() -> dict | None:
    """Get the public session value."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.PUBLIC_SPACE_GROUP_ID.name)


def get_public_session_id() -> str | None:
    """Get the public session id."""
    return _get_session_value(SessionKeySubName.AUTH, SessionKeyNameForAuth.PUBLIC_SESSION_ID.name)
