"""Handlers for the web app."""

import asyncio
import hashlib
import logging as log
import math
import random
from datetime import datetime
from typing import Any, List, Optional, Tuple

import streamlit as st
from docq import (
    config,
    domain,
    manage_documents,
    manage_organisations,
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
from docq.support.auth_utils import get_cache_auth_session, reset_cache_and_cookie_auth_session, set_cache_auth_session

from .constants import (
    MAX_NUMBER_OF_PERSONAL_DOCS,
    NUMBER_OF_MSGS_TO_LOAD,
    SessionKeyNameForAuth,
    SessionKeyNameForChat,
    SessionKeyNameForSettings,
    SessionKeySubName,
)
from .sessions import (
    _init_session_state,
    get_auth_session,
    get_authenticated_user_id,
    get_chat_session,
    get_public_space_group_id,
    get_selected_org_id,
    get_settings_session,
    get_username,
    reset_session_state,
    set_auth_session,
    set_chat_session,
    set_if_current_user_is_selected_org_admin,
    set_selected_org_id,
    set_settings_session,
)


def _set_session_state_configs(
    user_id: int,
    selected_org_id: int,
    name: str,
    username: str,
    anonymous: bool = False,
    super_admin: bool = False,
    selected_org_admin: bool = False,
    space_group_id: Optional[int] = None,
    public_session_id: Optional[str] = None,
) -> None:
    """Set the session state for the configs.

    Args:
        user_id (int): The user id.
        selected_org_id (str): The currently selected org id.
        name (str): The name.
        username (str): The username.
        anonymous (bool): Whether the user is anonymous defaults to False.
        super_admin (bool, optional): Whether the user is a super admin. Defaults to False.
        selected_org_admin (bool, optional): Whether the user is an org admin. Defaults to False.
        space_group_id (int, optional): The space group id. Defaults to None, required for anonymous/public sessions.
        public_session_id (str, optional): The public session id. Defaults to None, required for anonymous/public sessions.

    Returns:
        None
    """
    if anonymous:
        set_auth_session(
            {
                SessionKeyNameForAuth.NAME.name: name,
                SessionKeyNameForAuth.USERNAME.name: username,
                SessionKeyNameForAuth.SELECTED_ORG_ID.name: selected_org_id,
                SessionKeyNameForAuth.PUBLIC_SESSION_ID.name: public_session_id,
                SessionKeyNameForAuth.PUBLIC_SPACE_GROUP_ID.name: space_group_id,
                SessionKeyNameForAuth.ANONYMOUS.name: anonymous,
            },
            True,
        )
    else:
        # cache_session_state_configs(
        #     user_id=user_id,
        #     selected_org_id=selected_org_id,
        #     name=name,
        #     username=username,
        #     super_admin=super_admin,
        #     selected_org_admin=selected_org_admin,
        # )
        set_auth_session(
            {
                SessionKeyNameForAuth.ID.name: user_id,
                SessionKeyNameForAuth.NAME.name: name,
                SessionKeyNameForAuth.SUPER_ADMIN.name: super_admin,
                SessionKeyNameForAuth.USERNAME.name: username,
                SessionKeyNameForAuth.SELECTED_ORG_ID.name: selected_org_id,
                SessionKeyNameForAuth.SELECTED_ORG_ADMIN.name: selected_org_admin,
                SessionKeyNameForAuth.ANONYMOUS.name: anonymous,
            },
            True,
        )
    set_settings_session(
        {
            SessionKeyNameForSettings.SYSTEM.name: manage_settings.get_organisation_settings(org_id=selected_org_id),
            SessionKeyNameForSettings.USER.name: manage_settings.get_user_settings(
                org_id=selected_org_id, user_id=user_id
            ),
        }
    )


def handle_login(username: str, password: str) -> bool:
    """Handle login."""
    reset_session_state()
    reset_cache_and_cookie_auth_session()
    result = manage_users.authenticate(username, password)

    if result:
        current_user_id = result[0]
        member_orgs = manage_organisations.list_organisations(
            user_id=current_user_id
        )  # we can't use handle_list_orgs() here
        default_org_id = member_orgs[0][0]
        selected_org_admin = current_user_id in [x[0] for x in member_orgs[0][2]]
        log.info("Login result: %s", result)
        _set_session_state_configs(
            user_id=current_user_id,
            selected_org_id=default_org_id,
            name=result[1],
            username=username,
            super_admin=result[2],
            selected_org_admin=selected_org_admin,
        )
        log.info(st.session_state["_docq"])
        log.debug("auth session: %s", get_auth_session())
        return True
    else:
        return False


# def handle_set_cached_session_configs() -> None:
#     """Set cached auth configs."""
#     auth_configs = get_cache_auth_session()
#     if auth_configs and len(auth_configs) == 2:
#         _args, _kwargs = auth_configs
#         _set_session_state_configs(*_args, **_kwargs)


def handle_logout() -> None:
    """Handle logout."""
    reset_session_state()
    reset_cache_and_cookie_auth_session()
    log.info("Logout")


def _auto_login_feature_enabled() -> bool:
    """Check if auto login feature is enabled."""
    feature_enabled = False  # Only enable feature when explicitly enabled (default to Disabled)
    try:
        enabled_features = get_enabled_features()
        if enabled_features:
            feature_enabled = config.FeatureType.AUTO_LOGIN.name in enabled_features
        return feature_enabled
    except Exception as e:
        log.error("Failed to check if auto login is enabled: %s", e)
        return False


def handle_create_user() -> int:
    current_org_id = get_selected_org_id()
    result = manage_users.create_user(
        st.session_state["create_user_username"],
        st.session_state["create_user_password"],
        st.session_state["create_user_fullname"],
        False,
        False,
        current_org_id,
    )
    log.info("Create user with id: %s", result)
    return result


def handle_update_user(id_: int) -> bool:
    result = manage_users.update_user(
        id_,
        st.session_state[f"update_user_{id_}_username"],
        st.session_state[f"update_user_{id_}_password"],
        st.session_state[f"update_user_{id_}_fullname"],
        st.session_state[f"update_user_{id_}_super_admin"],
        False,
        st.session_state[f"update_user_{id_}_archived"],
    )
    log.info("Update user result: %s", result)
    return result


def list_users(name_match: str = None) -> list[tuple]:
    """Get a list of all users across all orgs.This should only be used with admin users and to add users to orgs.

    Args:
        name_match (str, optional): The name to match. Defaults to None.

    Returns:
        List[Tuple[int, str, str, str, bool, bool, datetime, datetime]]: The list of users [user id, username, fullname, super_admin, archived, created_at, updated_at].
    """
    return manage_users.list_users(name_match)


def list_users_by_current_org(username_match: str = None) -> list[tuple]:
    """Get a list of all users that are a member of an org.

    Args:
        org_id (int): The org id.
        username_match (str, optional): The name to match. Defaults to None.
    """
    org_id = get_selected_org_id()
    return manage_users.list_users_by_org(org_id=org_id, username_match=username_match)


def handle_create_user_group() -> int:
    org_id = get_selected_org_id()
    result = manage_user_groups.create_user_group(st.session_state["create_user_group_name"], org_id)
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
    org_id = get_selected_org_id()
    result = manage_user_groups.delete_user_group(id_, org_id)
    log.info("Update user group result: %s", result)
    return result


def list_user_groups(name_match: str = None) -> List[Tuple]:
    org_id = get_selected_org_id()
    return manage_user_groups.list_user_groups(org_id, name_match)


def list_public_spaces() -> List[Tuple]:
    """List public spaces in a space group."""
    space_group_id = get_public_space_group_id()
    return manage_spaces.list_public_spaces(space_group_id)


def handle_create_org() -> bool:
    """Create a new organization."""
    current_user_id = get_authenticated_user_id()
    name = st.session_state["create_org_name"]
    result = manage_organisations.create_organisation(name, current_user_id)

    log.info("Create org result: %s", result)
    return result


def handle_update_org(org_id: int) -> bool:
    """Update an existing organization."""
    name = st.session_state[f"update_org_{org_id}_name"]
    result = manage_organisations.update_organisation(org_id, name)
    manage_organisations.update_organisation_members(
        org_id, [x[0] for x in st.session_state[f"update_org_{org_id}_members"]]
    )
    log.info("Update org result: %s", result)
    return result


def handle_archive_org(id_: int) -> bool:
    """Archive an existing organization."""
    result = manage_organisations.archive_organisation(id_)
    log.info("Archive org result: %s", result)
    return result


def handle_list_orgs(name_match: str = None) -> List[Tuple]:
    """List all organizations.

    Returns:
         List[Tuple[int, str, List[Tuple[int, str]], datetime, datetime]]: The list of orgs [org_id, org_name, [user id, users fullname] created_at, updated_at].
    """
    current_user_id = get_authenticated_user_id()
    return manage_organisations.list_organisations(name_match=name_match, user_id=current_user_id)


def handle_org_selection_change(org_id: int) -> None:
    """Handle org selection change."""
    set_selected_org_id(org_id)
    set_if_current_user_is_selected_org_admin(org_id)


def handle_create_space_group() -> int:
    org_id = get_selected_org_id()
    result = manage_space_groups.create_space_group(
        org_id,
        st.session_state["create_space_group_name"],
        st.session_state["create_space_group_summary"],
    )
    log.info("Create space group with id: %s", result)
    return result


def handle_update_space_group(id_: int) -> bool:
    org_id = get_selected_org_id()
    result = manage_space_groups.update_space_group(
        id_,
        org_id,
        [x[0] for x in st.session_state[f"update_space_group_{id_}_members"]],
        st.session_state[f"update_space_group_{id_}_name"],
        st.session_state[f"update_space_group_{id_}_summary"],
    )
    log.info("Update space group result: %s", result)
    return result


def handle_delete_space_group(id_: int) -> bool:
    org_id = get_selected_org_id()
    result = manage_space_groups.delete_space_group(id_, org_id)
    log.info("Update space group result: %s", result)
    return result


def list_space_groups(name_match: str = None) -> List[Tuple]:
    org_id = get_selected_org_id()
    return manage_space_groups.list_space_groups(org_id, name_match)


def query_chat_history(feature: domain.FeatureKey) -> None:
    curr_cutoff = get_chat_session(feature.type_, SessionKeyNameForChat.CUTOFF)
    thread_id = get_chat_session(feature.type_, SessionKeyNameForChat.THREAD)
    history = run_queries.history(curr_cutoff, NUMBER_OF_MSGS_TO_LOAD, feature, thread_id)
    set_chat_session(
        history + get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY),
        feature.type_,
        SessionKeyNameForChat.HISTORY,
    )
    set_chat_session(history[0][3] if history else curr_cutoff, feature.type_, SessionKeyNameForChat.CUTOFF)


def _get_chat_spaces(feature: domain.FeatureKey) -> tuple[Optional[SpaceKey], List[SpaceKey]]:
    """Get chat spaces."""
    select_org_id = get_selected_org_id()

    personal_space = domain.SpaceKey(config.SpaceType.PERSONAL, feature.id_, select_org_id)

    if feature.type_ == config.FeatureType.ASK_SHARED:
        if not st.session_state["chat_personal_space"]:
            personal_space = None
        shared_spaces = [
            domain.SpaceKey(config.SpaceType.SHARED, s_[0], select_org_id)
            for s_ in st.session_state[f"chat_shared_spaces_{feature.value()}"]
        ]
        return personal_space, shared_spaces

    if feature.type_ == config.FeatureType.ASK_PUBLIC:
        personal_space = None
        shared_spaces = [domain.SpaceKey(config.SpaceType.SHARED, s_[0], select_org_id) for s_ in list_public_spaces()]
        return personal_space, shared_spaces

    shared_spaces = None
    return personal_space, shared_spaces


def handle_chat_input(feature: domain.FeatureKey) -> None:
    """Handle chat input."""
    req = st.session_state[f"chat_input_{feature.value()}"]

    space, spaces = _get_chat_spaces(feature)

    thread_id = get_chat_session(feature.type_, SessionKeyNameForChat.THREAD)

    result = run_queries.query(req, feature, thread_id, space, spaces)

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


def get_shared_space(id_: int) -> tuple[int, int, str, str, bool, str, dict, datetime, datetime]:
    org_id = get_selected_org_id()
    return manage_spaces.get_shared_space(id_, org_id)


def list_shared_spaces():
    user_id = get_authenticated_user_id()
    org_id = get_selected_org_id()
    return manage_spaces.list_shared_spaces(org_id, user_id)


def handle_archive_space(id_: int):
    manage_spaces.archive_space(id_)


def get_shared_space_permissions(id_: int) -> dict[SpaceAccessType, Any]:
    org_id = get_selected_org_id()
    permissions = manage_spaces.get_shared_space_permissions(id_, org_id)
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
    org_id = get_selected_org_id()
    result = manage_spaces.update_shared_space(
        id_,
        org_id,
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
    org_id = get_selected_org_id()
    space = manage_spaces.create_shared_space(
        org_id, st.session_state["create_space_name"], st.session_state["create_space_summary"], ds_type, ds_configs
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
    current_org_id = get_selected_org_id()
    return manage_settings.get_organisation_settings(org_id=current_org_id)


def get_enabled_features() -> list[domain.FeatureKey]:
    current_org_id = get_selected_org_id()
    return manage_settings.get_organisation_settings(
        org_id=current_org_id, key=config.SystemSettingsKey.ENABLED_FEATURES
    )


def handle_update_system_settings() -> None:
    current_org_id = get_selected_org_id()

    manage_settings.update_organisation_settings(
        {
            config.SystemSettingsKey.ENABLED_FEATURES.name: [
                f.name for f in st.session_state[f"system_settings_{config.SystemSettingsKey.ENABLED_FEATURES.name}"]
            ],
        },
        org_id=current_org_id,
    )
    set_settings_session(
        {
            config.SystemSettingsKey.ENABLED_FEATURES.name: [
                f.name for f in st.session_state[f"system_settings_{config.SystemSettingsKey.ENABLED_FEATURES.name}"]
            ],
        },
        SessionKeyNameForSettings.SYSTEM,
    )


def get_max_number_of_documents(type_: config.SpaceType):
    match type_:
        case config.SpaceType.PERSONAL:
            return MAX_NUMBER_OF_PERSONAL_DOCS
        case _:
            return math.inf


def _create_new_thread(feature: domain.FeatureKey) -> int:
    rnd = str(random.randint(1, 1000000))
    # TODO: add code to generate a topic name and update the DB after the first question is asked.
    topic = f"New thread {rnd}"
    thread_id = run_queries.create_history_thread(topic, feature)
    return thread_id


def prepare_for_chat(feature: domain.FeatureKey) -> None:
    """Prepare the session for chat. Load latest thread_id, cutoff, and history."""
    thread_id = 0
    log.debug("prepare_for_chat(): %s", get_chat_session(feature.type_))
    if SessionKeyNameForChat.THREAD.name not in get_chat_session(feature.type_):
        thread = run_queries.get_latest_thread(feature)
        thread_id = thread[0] if thread else _create_new_thread(feature)
        set_chat_session(thread_id, feature.type_, SessionKeyNameForChat.THREAD)

    if SessionKeyNameForChat.CUTOFF.name not in get_chat_session(feature.type_):
        set_chat_session(datetime.now(), feature.type_, SessionKeyNameForChat.CUTOFF)

    if SessionKeyNameForChat.HISTORY.name not in get_chat_session(feature.type_):
        set_chat_session([], feature.type_, SessionKeyNameForChat.HISTORY)

    if not get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY):
        query_chat_history(feature)
        if not get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY):
            set_chat_session(
                [("0", "Hi there! This is Docq, ask me anything.", False, datetime.now(), thread_id)],
                feature.type_,
                SessionKeyNameForChat.HISTORY,
            )


def handle_create_new_chat(feature: domain.FeatureKey) -> None:
    """Create a new chat session. Create a new thread_id and force reset session state."""
    thread_id = _create_new_thread(feature)
    set_chat_session(thread_id, feature.type_, SessionKeyNameForChat.THREAD)
    set_chat_session(datetime.now(), feature.type_, SessionKeyNameForChat.CUTOFF)
    set_chat_session(
        [("0", "Hi there! This is Docq, ask me anything.", False, datetime.now(), thread_id)],
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


def get_query_param(key: str, type_: type = int) -> Any | None:
    """Get query param and cast to type."""
    param = st.experimental_get_query_params().get(key, [None])[0]
    if param is None:
        return None
    if param == "default":
        return 1
    try:
        return type_(param)
    except ValueError:
        return None


def handle_public_session() -> None:
    """Handle public session."""
    session_id = get_query_param("session_id", str)
    org_id = get_query_param("param1")
    space_group_id = get_query_param("param2")

    reset_session_state()
    if org_id and session_id and space_group_id:
        _set_session_state_configs(
            user_id=None,
            selected_org_id=org_id,
            name=f"Anonymous {session_id}",
            username=f"anonymous_{session_id}",
            anonymous=True,
            space_group_id=space_group_id,
            public_session_id=session_id,
        )
    else:  # if no query params are provided, set space_group_id and public_session_id to -1 to disable ASK_PUBLIC feature
        _set_session_state_configs(
            user_id=None,
            selected_org_id=None,
            name=None,
            username=None,
            anonymous=True,
            space_group_id=-1,
            public_session_id=-1,
        )
