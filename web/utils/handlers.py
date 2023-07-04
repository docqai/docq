"""Handlers for the web app."""

import logging as log
import math
from datetime import datetime
from typing import List, Tuple

import streamlit as st
from docq import config, domain, run_queries
from docq import manage_documents as mdocuments
from docq import manage_settings as msettings
from docq import manage_spaces as mspaces
from docq import manage_users as musers
from docq.data_source.list import SPACE_DATA_SOURCES

from .constants import (
    MAX_NUMBER_OF_PERSONAL_DOCS,
    NUMBER_OF_MSGS_TO_LOAD,
    SessionKeyNameForAuth,
    SessionKeyNameForChat,
    SessionKeyNameForSettings,
)
from .sessions import get_chat_session, set_auth_session, set_chat_session, set_settings_session


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
        set_settings_session(
            {
                SessionKeyNameForSettings.SYSTEM.value: msettings.get_system_settings(),
                SessionKeyNameForSettings.USER.value: msettings.get_user_settings(result[0]),
            }
        )
        log.info(st.session_state["_docq"])
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


def list_users(username_match: str = None) -> list[tuple]:
    return musers.list_users(username_match)


def query_chat_history(feature: domain.FeatureKey) -> None:
    curr_cutoff = get_chat_session(feature.type_, SessionKeyNameForChat.CUTOFF)
    history = run_queries.history(curr_cutoff, NUMBER_OF_MSGS_TO_LOAD, feature)
    set_chat_session(
        history + get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY),
        feature.type_,
        SessionKeyNameForChat.HISTORY,
    )
    set_chat_session(history[0][3] if history else curr_cutoff, feature.type_, SessionKeyNameForChat.CUTOFF)


def handle_chat_input(feature: domain.FeatureKey) -> None:
    req = st.session_state[f"chat_input_{feature.value()}"]

    space = domain.SpaceKey(config.SpaceType.PERSONAL, feature.id_)

    spaces = (
        [domain.SpaceKey(config.SpaceType.SHARED, s_[0]) for s_ in st.session_state[f"chat_spaces_{feature.value()}"]]
        if feature.type_ == config.FeatureType.ASK_SHARED
        else None
    )
    result = run_queries.query(req, feature, space, spaces)

    get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY).extend(result)

    # st.session_state[f"chat_input_{feature.value()}"] = ""


def list_documents(space: domain.SpaceKey) -> list[tuple[str, int, int]]:
    return mdocuments.list_all(space)


def delete_document(filename: str, space: domain.SpaceKey) -> None:
    mdocuments.delete(filename, space)


def delete_all_documents(space: domain.SpaceKey) -> None:
    mdocuments.delete_all(space)


def handle_upload_file(space: domain.SpaceKey) -> None:
    files = st.session_state[f"uploaded_file_{space.value()}"]

    disp = st.empty()
    if not files:
        disp.warning("No file(s) selected, please select a file to upload")
        return None

    disp.empty()
    file_no = 0
    for file in files:
        try:
            file_no += 1
            disp.info(f"Uploading file {file_no} of {len(files)}")
            mdocuments.upload(file.name, file.getvalue(), space)
        except Exception as e:
            log.exception("Error uploading file %s", e)
            break
    # if all files are uploaded successfully
    else:
        disp.success(f"{len(files)} file(s) uploaded successfully")
        return None
    # if any error occurs
    disp.error("Error uploading file(s)")


def handle_change_temperature(type_: config.SpaceType):
    msettings.change_settings(type_.value, temperature=st.session_state[f"temperature_{type_}"])


def get_shared_space(id_: int) -> tuple[int, str, str, bool, str, dict, datetime, datetime]:
    return mspaces.get_shared_space(id_)


def list_shared_spaces():
    return mspaces.list_shared_spaces()


def handle_archive_space(id_: int):
    mspaces.archive_space(id_)


def _prepare_space_data_source(prefix: str) -> Tuple[str, dict]:
    ds_type = st.session_state[f"{prefix}ds_type"]
    ds_config_keys = list_space_data_source_choices()[ds_type]
    ds_configs = {key.key: st.session_state[f"{prefix}ds_config_{key.key}"] for key in ds_config_keys}
    return ds_type, ds_configs


def handle_update_space(id_: int) -> bool:
    ds_type, ds_configs = _prepare_space_data_source(f"update_space_{id_}_")
    result = mspaces.update_shared_space(
        id_,
        st.session_state[f"update_space_{id_}_name"],
        st.session_state[f"update_space_{id_}_summary"],
        st.session_state[f"update_space_{id_}_archived"],
        ds_type,
        ds_configs,
    )
    log.info("Update space result: %s", result)
    return result


def handle_create_space() -> int:
    ds_type, ds_configs = _prepare_space_data_source("create_space_")

    space_id = mspaces.create_shared_space(
        st.session_state["create_space_name"], st.session_state["create_space_summary"], ds_type, ds_configs
    )

    mdocuments.reindex(domain.SpaceKey(config.SpaceType.SHARED, space_id))
    return space_id


def list_space_data_source_choices() -> dict[str, List[domain.ConfigKey]]:
    return {key: value.get_config_keys() for key, value in SPACE_DATA_SOURCES.items()}


def get_system_settings() -> dict:
    return msettings.get_system_settings()


def get_enabled_features() -> list[domain.FeatureKey]:
    return msettings.get_system_settings(msettings.SystemSettingsKey.ENABLED_FEATURES)


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
    """Prepare the session for chat."""
    if SessionKeyNameForChat.CUTOFF.value not in get_chat_session(feature.type_):
        set_chat_session(datetime.now(), feature.type_, SessionKeyNameForChat.CUTOFF)

    if SessionKeyNameForChat.HISTORY.value not in get_chat_session(feature.type_):
        set_chat_session([], feature.type_, SessionKeyNameForChat.HISTORY)

    if not get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY):
        query_chat_history(feature)
        if not get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY):
            set_chat_session(
                [("0", "Hi there! This is Docq, ask me anything.", False, datetime.now())],
                feature.type_,
                SessionKeyNameForChat.HISTORY,
            )
