"""Handlers for the web app."""

import asyncio
import hashlib
import logging as log
import math
from datetime import datetime
from typing import Any, List, Tuple

import streamlit as st
from docq import (
    config,
    domain,
    manage_documents,
    manage_settings,
    manage_space_groups,
    manage_spaces,
    manage_user_groups,
    manage_users,
    run_queries,
)
from docq.access_control.main import SpaceAccessor, SpaceAccessType
from docq.data_source.list import SpaceDataSources
from docq.domain import DocumentListItem, SpaceKey

from .constants import (
    MAX_NUMBER_OF_PERSONAL_DOCS,
    NUMBER_OF_MSGS_TO_LOAD,
    SessionKeyNameForAuth,
    SessionKeyNameForChat,
    SessionKeyNameForSettings,
)
from .sessions import (
    get_authenticated_user_id,
    get_chat_session,
    get_username,
    set_auth_session,
    set_chat_session,
    set_settings_session,
)


def handle_login(username: str, password: str) -> bool:
    """Handle login."""
    result = manage_users.authenticate(username, password)
    log.info("Login result: %s", result)
    if result:
        set_auth_session(
            {
                SessionKeyNameForAuth.ID.name: result[0],
                SessionKeyNameForAuth.NAME.name: result[1],
                SessionKeyNameForAuth.ADMIN.name: result[2],
                SessionKeyNameForAuth.USERNAME.name: result[3],
            }
        )
        set_settings_session(
            {
                SessionKeyNameForSettings.SYSTEM.name: manage_settings.get_system_settings(),
                SessionKeyNameForSettings.USER.name: manage_settings.get_user_settings(result[0]),
            }
        )
        log.info(st.session_state["_docq"])
        return True
    else:
        return False


def handle_logout() -> None:
    set_auth_session()


def handle_create_user() -> int:
    result = manage_users.create_user(
        st.session_state["create_user_username"],
        st.session_state["create_user_password"],
        st.session_state["create_user_fullname"],
        st.session_state["create_user_admin"],
    )
    log.info("Create user with id: %s", result)
    return result


def handle_update_user(id_: int) -> bool:
    result = manage_users.update_user(
        id_,
        st.session_state[f"update_user_{id_}_username"],
        st.session_state[f"update_user_{id_}_password"],
        st.session_state[f"update_user_{id_}_fullname"],
        st.session_state[f"update_user_{id_}_admin"],
        st.session_state[f"update_user_{id_}_archived"],
    )
    log.info("Update user result: %s", result)
    return result


def list_users(name_match: str = None) -> list[tuple]:
    return manage_users.list_users(name_match)


def handle_create_user_group() -> int:
    result = manage_user_groups.create_user_group(
        st.session_state["create_user_group_name"],
    )
    log.info("Create user group result: %s", result)
    return result


def handle_update_user_group(id_: int) -> bool:
    result = manage_user_groups.update_user_group(
        id_,
        [x[0] for x in st.session_state[f"update_user_group_{id_}_members"]],
        st.session_state[f"update_user_group_{id_}_name"],
    )
    log.info("Update user group result: %s", result)
    return result


def handle_delete_user_group(id_: int) -> bool:
    result = manage_user_groups.delete_user_group(id_)
    log.info("Update user group result: %s", result)
    return result


def list_user_groups(name_match: str = None) -> List[Tuple]:
    return manage_user_groups.list_user_groups(name_match)


def handle_create_space_group() -> int:
    result = manage_space_groups.create_space_group(
        st.session_state["create_space_group_name"],
        st.session_state["create_space_group_summary"],
    )
    log.info("Create space group with id: %s", result)
    return result


def handle_update_space_group(id_: int) -> bool:
    result = manage_space_groups.update_space_group(
        id_,
        [x[0] for x in st.session_state[f"update_space_group_{id_}_members"]],
        st.session_state[f"update_space_group_{id_}_name"],
        st.session_state[f"update_space_group_{id_}_summary"],
    )
    log.info("Update space group result: %s", result)
    return result


def handle_delete_space_group(id_: int) -> bool:
    result = manage_space_groups.delete_space_group(id_)
    log.info("Update space group result: %s", result)
    return result


def list_space_groups(name_match: str = None) -> List[Tuple]:
    return manage_space_groups.list_space_groups(name_match)


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


def handle_list_documents(space: domain.SpaceKey) -> List[DocumentListItem]:
    return manage_spaces.list_documents(space)


def handle_delete_document(filename: str, space: domain.SpaceKey) -> None:
    manage_documents.delete(filename, space)


def handle_delete_all_documents(space: domain.SpaceKey) -> None:
    manage_documents.delete_all(space)


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
            manage_documents.upload(file.name, file.getvalue(), space)
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
    manage_settings.change_settings(type_.name, temperature=st.session_state[f"temperature_{type_.name}"])


def get_shared_space(id_: int) -> tuple[int, str, str, bool, str, dict, datetime, datetime]:
    return manage_spaces.get_shared_space(id_)


def list_shared_spaces():
    user_id = get_authenticated_user_id()
    return manage_spaces.list_shared_spaces(user_id)


def handle_archive_space(id_: int):
    manage_spaces.archive_space(id_)


def get_shared_space_permissions(id_: int) -> dict[SpaceAccessType, Any]:
    permissions = manage_spaces.get_shared_space_permissions(id_)
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
    ds_type = st.session_state[f"{prefix}ds_type"][0]
    ds_config_keys = SpaceDataSources.__members__[ds_type].value.get_config_keys()
    ds_configs = {key.key: st.session_state[f"{prefix}ds_config_{key.key}"] for key in ds_config_keys}
    return ds_type, ds_configs


def handle_update_space_details(id_: int) -> bool:
    ds_type, ds_configs = _prepare_space_data_source(f"update_space_details_{id_}_")
    result = manage_spaces.update_shared_space(
        id_,
        st.session_state[f"update_space_details_{id_}_name"],
        st.session_state[f"update_space_details_{id_}_summary"],
        st.session_state[f"update_space_details_{id_}_archived"],
        ds_type,  # The actual update on data source has been disabled on UI; This may be enabled in the future.
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
    return manage_spaces.update_shared_space_permissions(id_, permissions)


def handle_create_space() -> SpaceKey:
    ds_type, ds_configs = _prepare_space_data_source("create_space_")

    space = manage_spaces.create_shared_space(
        st.session_state["create_space_name"], st.session_state["create_space_summary"], ds_type, ds_configs
    )
    return space


def handle_reindex_space(space: SpaceKey) -> None:
    log.debug("handle re-indexing space: %s", space)
    manage_spaces.reindex(space)


def get_space_data_source(space: SpaceKey) -> Tuple[str, dict]:
    return manage_spaces.get_space_data_source(space)


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
    return manage_settings.get_system_settings()


def get_enabled_features() -> list[domain.FeatureKey]:
    return manage_settings.get_system_settings(config.SystemSettingsKey.ENABLED_FEATURES)


def handle_update_system_settings() -> None:
    manage_settings.update_system_settings(
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

def handle_get_gravatar_url() -> str:
    """Get Gravatar URL for the specified email."""
    email = get_username()
    if email is None:
        email = "example@example.com"
    size, default, rating = 200, "identicon", "g"
    email_hash = hashlib.md5(email.lower().encode("utf-8")).hexdigest()  # noqa: S324
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d={default}&r={rating}"
