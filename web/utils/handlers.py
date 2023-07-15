"""Handlers for the web app."""

import logging as log
import math
from datetime import datetime
from typing import Any, List, Tuple

import streamlit as st
from docq import config, domain, run_queries
from docq import manage_documents as mdocuments
from docq import manage_groups as mgroups
from docq import manage_settings as msettings
from docq import manage_spaces as mspaces
from docq import manage_users as musers
from docq.access_control.main import SpaceAccessor, SpaceAccessType
from docq.data_source.list import SpaceDataSources
from docq.domain import SpaceKey

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
                SessionKeyNameForAuth.ID.name: result[0],
                SessionKeyNameForAuth.NAME.name: result[1],
                SessionKeyNameForAuth.ADMIN.name: result[2],
            }
        )
        set_settings_session(
            {
                SessionKeyNameForSettings.SYSTEM.name: msettings.get_system_settings(),
                SessionKeyNameForSettings.USER.name: msettings.get_user_settings(result[0]),
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


def handle_create_group() -> int:
    result = mgroups.create_group(
        st.session_state["create_group_name"],
    )
    log.info("Create group with id: %s", result)
    return result


def handle_update_group(id_: int) -> bool:
    result = mgroups.update_group(
        id_,
        [x[0] for x in st.session_state[f"update_group_{id_}_members"]],
        st.session_state[f"update_group_{id_}_name"],
    )
    log.info("Update group result: %s", result)
    return result


def handle_delete_group(id_: int) -> bool:
    result = mgroups.delete_group(id_)
    log.info("Update group result: %s", result)
    return result


def list_users(username_match: str = None) -> list[tuple]:
    return musers.list_users(username_match)


def list_selected_users(user_ids: List[int]) -> list[tuple]:
    return musers.list_selected_users(user_ids)


def list_groups(groupname_match: str = None) -> list[tuple]:
    return mgroups.list_groups(groupname_match)


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

    space = (
        None
        if feature.type_ == config.FeatureType.ASK_SHARED and not st.session_state["chat_personal_space"]
        else domain.SpaceKey(config.SpaceType.PERSONAL, feature.id_)
    )

    spaces = (
        [
            domain.SpaceKey(config.SpaceType.SHARED, s_[0])
            for s_ in st.session_state[f"chat_shared_spaces_{feature.value()}"]
        ]
        if feature.type_ == config.FeatureType.ASK_SHARED
        else None
    )
    result = run_queries.query(req, feature, space, spaces)

    get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY).extend(result)


def handle_list_documents(space: domain.SpaceKey) -> list[tuple[str, int, int]]:
    return mspaces.list_documents(space)


def handle_delete_document(filename: str, space: domain.SpaceKey) -> None:
    mdocuments.delete(filename, space)


def handle_delete_all_documents(space: domain.SpaceKey) -> None:
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
    msettings.change_settings(type_.name, temperature=st.session_state[f"temperature_{type_.name}"])


def get_shared_space(id_: int) -> tuple[int, str, str, bool, str, dict, datetime, datetime]:
    return mspaces.get_shared_space(id_)


def list_shared_spaces():
    return mspaces.list_shared_spaces()


def handle_archive_space(id_: int):
    mspaces.archive_space(id_)


def get_shared_space_permissions(id_: int) -> dict[SpaceAccessType, Any]:
    permissions = mspaces.get_shared_space_permissions(id_)
    results = {
        SpaceAccessType.PUBLIC: any(p.type_ == SpaceAccessType.PUBLIC for p in permissions),
        SpaceAccessType.USER: [
            (p.accessor_id, p.accessor_name) for p in permissions if p.type_ == SpaceAccessType.USER
        ],
        SpaceAccessType.GROUP: [
            (p.accessor_id, p.accessor_name) for p in permissions if p.type_ == SpaceAccessType.GROUP
        ],
    }
    log.debug("Get shared space permissions: %s", results)
    return results


def _prepare_space_data_source(prefix: str) -> Tuple[str, dict]:
    ds_type = (
        st.session_state[f"{prefix}ds_type"][0] if prefix == "create_space_" else st.session_state[f"{prefix}ds_type"]
    )
    log.debug(">>> ds_type:%s, prefic:%s, %s", ds_type, prefix, st.session_state[f"{prefix}ds_type"])
    ds_config_keys = SpaceDataSources.__members__[ds_type].value.get_config_keys()
    ds_configs = {key.key: st.session_state[f"{prefix}ds_config_{key.key}"] for key in ds_config_keys}
    return ds_type, ds_configs


def handle_update_space_details(id_: int) -> bool:
    ds_type, ds_configs = _prepare_space_data_source(f"update_space_details_{id_}_")
    result = mspaces.update_shared_space(
        id_,
        st.session_state[f"update_space_details_{id_}_name"],
        st.session_state[f"update_space_details_{id_}_summary"],
        st.session_state[f"update_space_details_{id_}_archived"],
        ds_type,
        ds_configs,
    )
    log.info("Update space details result: %s", result)
    return result


def handle_manage_space_permissions(id_: int) -> bool:
    permissions = []
    if st.session_state[f"manage_space_permissions_{id_}_{SpaceAccessType.PUBLIC.name}"] is True:
        permissions.append(SpaceAccessor(SpaceAccessType.PUBLIC))

    for k in [SpaceAccessType.USER, SpaceAccessType.GROUP]:
        for accessor_id, accessor_name, *_ in st.session_state[f"manage_space_permissions_{id_}_{k.name}"]:
            permissions.append(SpaceAccessor(k, accessor_id, accessor_name))

    log.debug("Manage space permissions: %s", permissions)
    return mspaces.update_shared_space_permissions(id_, permissions)


def handle_create_space() -> SpaceKey:
    ds_type, ds_configs = _prepare_space_data_source("create_space_")

    space = mspaces.create_shared_space(
        st.session_state["create_space_name"], st.session_state["create_space_summary"], ds_type, ds_configs
    )
    return space


def handle_reindex_space(space: SpaceKey) -> None:
    mspaces.reindex(space)


def get_space_data_source(space: SpaceKey) -> Tuple[str, dict]:
    return mspaces.get_space_data_source(space)


def list_space_data_source_choices() -> List[Tuple[str, str, List[domain.ConfigKey]]]:
    return [
        (key, value.value.get_name(), value.value.get_config_keys())
        for key, value in SpaceDataSources.__members__.items()
    ]


def get_space_data_source_choice_by_type(type_: str) -> Tuple[str, str, List[domain.ConfigKey]]:
    return (
        type_,
        SpaceDataSources.__members__[type_].value.get_name(),
        SpaceDataSources.__members__[type_].value.get_config_keys(),
    )


def get_system_settings() -> dict:
    return msettings.get_system_settings()


def get_enabled_features() -> list[domain.FeatureKey]:
    return msettings.get_system_settings(config.SystemSettingsKey.ENABLED_FEATURES)


def handle_update_system_settings() -> None:
    msettings.update_system_settings(
        {
            config.SystemSettingsKey.ENABLED_FEATURES.name: [
                f.name for f in st.session_state[f"system_settings_{config.SystemSettingsKey.ENABLED_FEATURES.name}"]
            ],
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
    if SessionKeyNameForChat.CUTOFF.name not in get_chat_session(feature.type_):
        set_chat_session(datetime.now(), feature.type_, SessionKeyNameForChat.CUTOFF)

    if SessionKeyNameForChat.HISTORY.name not in get_chat_session(feature.type_):
        set_chat_session([], feature.type_, SessionKeyNameForChat.HISTORY)

    if not get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY):
        query_chat_history(feature)
        if not get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY):
            set_chat_session(
                [("0", "Hi there! This is Docq, ask me anything.", False, datetime.now())],
                feature.type_,
                SessionKeyNameForChat.HISTORY,
            )
