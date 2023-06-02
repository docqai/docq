"""Handlers for the web app."""

import logging as log
import math
from datetime import datetime
from typing import Any, Optional

import streamlit as st
from docq import config, domain, run_queries
from docq import manage_documents as mdocuments
from docq import manage_settings as msettings
from docq import manage_sharing as msharing
from docq import manage_spaces as mspaces
from docq import manage_users as musers

from .constants import (
    MAX_NUMBER_OF_PERSONAL_DOCS,
    NUMBER_OF_MSGS_TO_LOAD,
    SESSION_KEY_NAME_DOCQ,
    SessionKeyNameForAuth,
    SessionKeyNameForChat,
    SessionKeySubName,
)


def __init_session_state() -> None:
    if SESSION_KEY_NAME_DOCQ not in st.session_state:
        st.session_state[SESSION_KEY_NAME_DOCQ] = {}
    for n in SessionKeySubName:
        if n.value not in st.session_state[SESSION_KEY_NAME_DOCQ]:
            st.session_state[SESSION_KEY_NAME_DOCQ][n.value] = {}
    for n in config.FeatureType:
        if n.value not in st.session_state[SESSION_KEY_NAME_DOCQ]:
            st.session_state[SESSION_KEY_NAME_DOCQ][n.value] = {}


def get_session_state(type_: config.FeatureType = None, key_: Optional[SessionKeyNameForChat] = None) -> Any:
    __init_session_state()
    if type_ is None and key_ is None:
        return st.session_state[SESSION_KEY_NAME_DOCQ]
    elif key_ is None:
        return st.session_state[SESSION_KEY_NAME_DOCQ][type_.value]
    else:
        return st.session_state[SESSION_KEY_NAME_DOCQ][type_.value][key_.value]


def set_session_state(val: Any, type_: config.FeatureType = None, key_: Optional[SessionKeyNameForChat] = None) -> None:
    __init_session_state()
    if type_ is None and key_ is None:
        st.session_state[SESSION_KEY_NAME_DOCQ] = val
    elif key_ is None:
        st.session_state[SESSION_KEY_NAME_DOCQ][type_.value] = val
    else:
        st.session_state[SESSION_KEY_NAME_DOCQ][type_.value][key_.value] = val

    log.debug(st.session_state[SESSION_KEY_NAME_DOCQ])


def get_auth_session() -> dict:
    __init_session_state()
    return st.session_state[SESSION_KEY_NAME_DOCQ][SessionKeySubName.AUTH.value]


def set_auth_session(val: Optional[dict] = None) -> None:
    __init_session_state()
    st.session_state[SESSION_KEY_NAME_DOCQ][SessionKeySubName.AUTH.value] = val


def get_authenticated_user_id() -> Optional[int]:
    return get_auth_session().get(SessionKeyNameForAuth.ID.value)


def handle_login(username: str, password: str) -> bool:
    result = musers.authenticate(username, password)
    log.info("Login result: %s", result)
    if result:
        set_auth_session(
            {
                SessionKeyNameForAuth.ID.value: result[0],
                SessionKeyNameForAuth.NAME.value: result[1],
                SessionKeyNameForAuth.ADMIN.value: result[2],
            }
        )
        return True
    else:
        return False


def handle_logout() -> None:
    set_auth_session()


def handle_create_user() -> int:
    result = musers.create_user(
        st.session_state["create_user_username"],
        st.session_state["create_user_password"],
        st.session_state["create_user_fullname"],
        st.session_state["create_user_admin"],
    )
    log.info("Create user with id: %s", result)
    return result


def handle_update_user(id_: int) -> bool:
    result = musers.update_user(
        id_,
        st.session_state[f"update_user_{id_}_username"],
        st.session_state[f"update_user_{id_}_password"],
        st.session_state[f"update_user_{id_}_fullname"],
        st.session_state[f"update_user_{id_}_admin"],
        st.session_state[f"update_user_{id_}_archived"],
    )
    log.info("Update user result: %s", result)
    return result


def list_users(username_match: Optional[str] = None) -> list[tuple]:
    return musers.list_users(username_match)


def query_chat_history(feature: domain.FeatureKey) -> None:
    curr_cutoff = get_session_state(feature.type_, SessionKeyNameForChat.CUTOFF)
    history = run_queries.history(curr_cutoff, NUMBER_OF_MSGS_TO_LOAD, feature)
    set_session_state(
        history + get_session_state(feature.type_, SessionKeyNameForChat.HISTORY),
        feature.type_,
        SessionKeyNameForChat.HISTORY,
    )
    set_session_state(history[0][3] if history else curr_cutoff, feature.type_, SessionKeyNameForChat.CUTOFF)


def handle_chat_input(feature: domain.FeatureKey) -> None:
    req = st.session_state[f"chat_input_{feature.value()}"]

    space = domain.SpaceKey(config.SpaceType.PERSONAL, feature.id_)

    spaces = (
        [domain.SpaceKey(config.SpaceType.SHARED, s_[0]) for s_ in st.session_state[f"chat_spaces_{feature.value()}"]]
        if feature.type_ == config.FeatureType.ASK_SHARED
        else None
    )
    result = run_queries.query(req, feature, space, spaces)

    get_session_state(feature.type_, SessionKeyNameForChat.HISTORY).extend(result)

    st.session_state[f"chat_input_{feature.value()}"] = ""


def list_documents(space: domain.SpaceKey) -> list[tuple[str, int, int]]:
    return mdocuments.list_all(space)


def delete_document(filename: str, space: domain.SpaceKey) -> None:
    mdocuments.delete(filename, space)


def delete_all_documents(space: domain.SpaceKey) -> None:
    mdocuments.delete_all(space)


def handle_upload_file(space: domain.SpaceKey) -> None:
    file = st.session_state[f"uploaded_file_{space.value()}"]
    mdocuments.upload(file.name, file.getvalue(), space)


def handle_change_temperature(type_: config.SpaceType):
    msettings.change_settings(type_.value, temperature=st.session_state[f"temperature_{type_}"])


def get_shared_space(id_: int) -> tuple[int, str, str, bool, datetime, datetime]:
    return mspaces.get_shared_space(id_)


def list_shared_spaces():
    return mspaces.list_shared_spaces()


def handle_archive_space(id_: int):
    mspaces.archive_space(id_)


def handle_update_space(id_: int) -> bool:
    result = mspaces.update_shared_space(
        id_,
        st.session_state[f"update_space_{id_}_name"],
        st.session_state[f"update_space_{id_}_summary"],
        st.session_state[f"update_space_{id_}_archived"],
    )
    log.info("Update space result: %s", result)
    return result


def handle_create_space() -> int:
    return mspaces.create_shared_space(st.session_state["create_space_name"], st.session_state["create_space_summary"])


def get_system_settings() -> dict:
    return msettings.get_system_settings()


def handle_update_system_settings() -> None:
    msettings.update_system_settings(
        {
            msettings.SystemSettingsKey.ENABLED_FEATURES.value: st.session_state["system_settings_enabled_features"],
        }
    )


def get_max_number_of_documents(type_: config.SpaceType):
    match type_:
        case config.SpaceType.PERSONAL:
            return MAX_NUMBER_OF_PERSONAL_DOCS
        case _:
            return math.inf


def prepare_for_chat(feature: domain.FeatureKey) -> None:
    """Initialises the session state for the given feature."""
    __init_session_state()

    if SessionKeyNameForChat.CUTOFF.value not in get_session_state(feature.type_):
        set_session_state(datetime.now(), feature.type_, SessionKeyNameForChat.CUTOFF)

    if SessionKeyNameForChat.HISTORY.value not in get_session_state(feature.type_):
        set_session_state([], feature.type_, SessionKeyNameForChat.HISTORY)

    if not get_session_state(feature.type_, SessionKeyNameForChat.HISTORY):
        query_chat_history(feature)
        if not get_session_state(feature.type_, SessionKeyNameForChat.HISTORY):
            set_session_state(
                [("0", "Hi there! This is Docq, ask me anything.", False, datetime.now())],
                feature.type_,
                SessionKeyNameForChat.HISTORY,
            )
