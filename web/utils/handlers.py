"""Handlers for the web app."""

import base64
import hashlib
import logging as log
import math
import random
from datetime import datetime
from typing import Any, List, Optional, Tuple
from urllib.parse import unquote_plus

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
from docq.extensions import ExtensionContext, _registered_extensions
from docq.model_selection.main import ModelUsageSettingsCollection, get_saved_model_settings_collection
from docq.services.smtp_service import mailer_ready, send_verification_email
from docq.support.auth_utils import reset_cache_and_cookie_auth_session
from opentelemetry import baggage, trace

from .constants import (
    MAX_NUMBER_OF_PERSONAL_DOCS,
    NUMBER_OF_MSGS_TO_LOAD,
    SessionKeyNameForAuth,
    SessionKeyNameForChat,
    SessionKeyNameForSettings,
)
from .error_ui import set_error_state_for_ui
from .sessions import (
    get_auth_session,
    get_authenticated_user_id,
    get_chat_session,
    get_public_space_group_id,
    get_selected_org_id,
    get_username,
    is_current_user_selected_org_admin,
    reset_session_state,
    set_auth_session,
    set_chat_session,
    set_if_current_user_is_selected_org_admin,
    set_selected_org_id,
    set_settings_session,
)

tracer = trace.get_tracer("docq.web.handler")


@tracer.start_as_current_span("_set_session_state_configs")
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


@tracer.start_as_current_span("_default_org_id")
def _default_org_id(
    member_orgs: List[Tuple[int, str, List[Tuple[int, str, bool]], datetime, datetime]],
    authd_user: Tuple[int, str, bool, str],
) -> int:
    """Get the default org id."""
    result = member_orgs[0][0]
    firstname = authd_user[1].split(" ")[0]
    log.debug("firstname arg: %s", firstname)
    for x in member_orgs:
        if x[1].startswith(firstname):
            log.debug("firstname '%s' in org name: %s", firstname, x[1])
            result = x[0]
    return result


@tracer.start_as_current_span("handle_login")
def handle_login(username: str, password: str) -> bool:
    """Handle login."""
    span = trace.get_current_span()
    reset_session_state()
    reset_cache_and_cookie_auth_session()
    result = manage_users.authenticate(username, password)
    if result:
        current_user_id = result[0]
        span.add_event("authenticated", {"result": "successful", "username": username, "user_id": current_user_id})
        member_orgs = manage_organisations.list_organisations(
            user_id=current_user_id
        )  # we can't use handle_list_orgs() here
        log.debug("handle_login(): member_orgs: %s", member_orgs)
        default_org_id = _default_org_id(member_orgs, result)
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
        baggage.set_baggage("current_user_id", str(current_user_id))
        baggage.set_baggage("selected_org_id", str(default_org_id))
        baggage.set_baggage("selected_org_admin", str(selected_org_admin))
        baggage.set_baggage("username", username)
        span.set_attributes(
            {
                "auth.selected_org_id": str(default_org_id),
                "auth.selected_org_admin": str(selected_org_admin),
                "auth.user_id": str(current_user_id),
                "auth.username": username,
            }
        )
        log.info(st.session_state["_docq"])
        log.debug("auth session: %s", get_auth_session())
        return True
    else:
        span.add_event("authenticated", {"result": "failed", "username": username})
        return False


def handle_logout() -> None:
    """Handle logout."""
    reset_session_state()
    reset_cache_and_cookie_auth_session()
    log.info("Logout")


def handle_fire_extensions_callbacks(event_name: str, _context: Optional[ExtensionContext] = None) -> None:
    """Handle fire extensions callbacks.

    This function can be called form anywhere in the web code base to fire callbacks event that extensions can hook into.

    Args:
        event_name (str): The name of the event. format <webui|webapi|dal><thing>.<action as past tense verb>
        _context (ExtensionContext): The context of the event.
    """
    log.debug("fire_extensions_callbacks() called with event: %s", event_name)

    ctx = _context or ExtensionContext()
    ctx.extension_register = _registered_extensions
    log.debug("About the call callback_handler() for '%s' extensions", len(_registered_extensions.keys()))
    for _, ext_cls in _registered_extensions.items():
        log.debug("%s", ext_cls.class_name())
        ext_cls.callback_handler(event_name, ctx)


def handle_create_user() -> int:
    """Handle create user. If the user already exists, just adds the user to the currently selected org else create and add.

    Only org admins are allowed to create users.

    Return:
        int: The user id.
        PermissionError: If the current user is not an org admin of the currently selected org.
    """
    user_id = None
    try:
        if not is_current_user_selected_org_admin():
            raise PermissionError(
                "Only org admins are allowed to create users. The current user is not an org admin of the currently selected org."
            )
        current_org_id = get_selected_org_id()
        create_user_username = st.session_state["create_user_username"]
        user = manage_users.get_user(username=create_user_username)
        log.debug("user: %s", user)
        if user:
            if not manage_users.user_is_org_member(current_org_id, user[0]):
                # user exists but not already member of org, so add to org
                log.info("User already exists, so just added to org_id: %s", current_org_id)
                user_added = manage_users.add_organisation_member(current_org_id, user[0])
                if not user_added:
                    raise Exception("Failed to add user to org")
            else:
                log.info("User already exists and is already a member of org_id: %s. No op.", current_org_id)
            user_id = user[0]
        else:
            # create a user and add to org
            user_id = manage_users.create_user(
                create_user_username,
                st.session_state["create_user_password"],
                st.session_state["create_user_fullname"],
                False,
                False,
                current_org_id,
            )
            manage_users.set_user_as_verified(user_id)
            log.info("Create user with id: %s and added to org_id: %s", user_id, current_org_id)
    except Exception as e:
        set_error_state_for_ui(key="create_user", error=str(e), message="Failed to create user.", trace_id="")
        log.error("handle_create_user() error: %s", e)
    return user_id


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


def handle_check_user_exists(username: str) -> bool:
    """Check if a user with a given username (email) exists."""
    return manage_users.get_user(username=username) is not None


def handle_user_signup() -> bool:
    """Handle user signup."""
    form = "user-signup"
    validator = st.session_state.get(f"{form}-validator", st.empty())
    try:
        username = st.session_state[f"{form}-email"]
        fullname = st.session_state[f"{form}-name"]
        user_id = manage_users.create_user(
            username=username,
            password=st.session_state[f"{form}-password"],
            fullname=fullname,
        )
        user_orgs = manage_organisations.list_organisations(user_id=user_id)

        _ctx = ExtensionContext(
            data={"username": username, "fullname": fullname, "user_id": user_id, "org_id": user_orgs[0][0]}
        )
        handle_fire_extensions_callbacks("webui.handle_user_signup.user_created", _ctx)
        if user_id:
            send_verification_email(username, fullname, user_id)
            validator.success(
                "A verification email has been sent to your email address. Please verify your email before logging in."
            )
        log.info("User signup result: %s", user_id)
        handle_fire_extensions_callbacks("webui.handle_user_signup.verification_email_sent", _ctx)
        return True
    except Exception as e:
        validator.error("Failed to create user.")
        log.error("handle_user_signup() error: %s", e, stack_info=True)
        return False


def handle_resend_email_verification(username: str) -> bool:
    """Handle resend email verification."""
    user_id, _, fullname, *_ = manage_users.get_user(username=username)
    if user_id and fullname:
        send_verification_email(username, fullname, user_id)
        log.info("Verification email sent: %s", {username, user_id, fullname})
        return True
    return False


def _verify_timestamp(timestamp: str) -> bool:
    """Verify the timestamp."""
    try:
        return int(float(timestamp)) > int(datetime.now().timestamp()) - 3600
    except Exception as e:
        log.exception("Error verifying timestamp: %s", e)
        return False


def _verify_hash(user_id: str, timestamp: str, hash_: str) -> bool:
    """Verify the hash."""
    try:
        return hashlib.sha256(f"{user_id}::{timestamp}".encode("utf-8")).hexdigest() == hash_
    except Exception as e:
        log.exception("Error verifying hash: %s", e)
        return False


def handle_verify_email() -> bool:
    """Handle email verification."""
    user_info = st.experimental_get_query_params().get("token", [None])[0]
    if user_info:
        decoded = unquote_plus(base64.b64decode(user_info).decode("utf-8"))
        user_id, timestamp, hash_ = decoded.split("::")
        if _verify_timestamp(timestamp) and _verify_hash(user_id, timestamp, hash_):
            manage_users.set_user_as_verified(int(user_id))
            return True
    return False


def handle_check_account_activated(username: str) -> bool:
    """Check if the account is activated."""
    return manage_users.check_account_activated(username)


def handle_check_mailer_ready() -> bool:
    """Check if the mailer is ready."""
    return mailer_ready()


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
    result = False
    try:
        current_user_id = get_authenticated_user_id()
        name = st.session_state["create_org_name"]
        result = manage_organisations.create_organisation(name, current_user_id)

        log.info("Create org result: %s", result)
    except Exception as e:
        log.error("handle_create_org() error: %s", e)
        set_error_state_for_ui(key="create_org", error=str(e), message="Failed to create org.", trace_id="")
    return result


def handle_update_org(org_id: int) -> bool:
    """Update an existing organization."""
    name = st.session_state[f"update_org_{org_id}_name"]
    result = manage_organisations.update_organisation(org_id, name)
    log.debug("member state: %s", st.session_state[f"update_org_{org_id}_members"])
    manage_users.update_organisation_members(
        org_id, [(x[0], x[2]) for x in st.session_state[f"update_org_{org_id}_members"]]
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
         List[Tuple[int, str, List[Tuple[int, str, bool]], datetime, datetime]]: The list of orgs [org_id, org_name, [user id, users fullname, org admin] created_at, updated_at].
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


@tracer.start_as_current_span("query_chat_history")
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


@tracer.start_as_current_span("_get_chat_spaces")
def _get_chat_spaces(feature: domain.FeatureKey) -> tuple[Optional[SpaceKey], List[SpaceKey]]:
    """Get chat spaces."""
    select_org_id = get_selected_org_id()

    personal_space = domain.SpaceKey(config.SpaceType.PERSONAL, feature.id_, select_org_id)
    shared_spaces = manage_spaces.get_shared_spaces(
        [s_[0] for s_ in st.session_state[f"chat_shared_spaces_{feature.value()}"]]
    )

    if feature.type_ == config.OrganisationFeatureType.ASK_SHARED:
        if not st.session_state["chat_personal_space"]:
            personal_space = None
        shared_spaces = [
            domain.SpaceKey(config.SpaceType.SHARED, s_[0], select_org_id, summary=s_[3])
            # for s_ in st.session_state[f"chat_shared_spaces_{feature.value()}"]
            for s_ in shared_spaces
        ]
        return personal_space, shared_spaces

    if feature.type_ == config.OrganisationFeatureType.ASK_PUBLIC:
        personal_space = None
        shared_spaces = [domain.SpaceKey(config.SpaceType.SHARED, s_[0], select_org_id) for s_ in list_public_spaces()]
        return personal_space, shared_spaces

    shared_spaces = None
    return personal_space, shared_spaces


@tracer.start_as_current_span("handle_chat_input")
def handle_chat_input(feature: domain.FeatureKey) -> None:
    """Handle chat input."""
    req = st.session_state[f"chat_input_{feature.value()}"]
    space, spaces = None, None
    if feature.type_ is not config.OrganisationFeatureType.CHAT_PRIVATE:
        space, spaces = _get_chat_spaces(feature)

    thread_id = get_chat_session(feature.type_, SessionKeyNameForChat.THREAD)
    if thread_id is None:
        raise ValueError("Thread id in session state was None")
    saved_model_settings = get_saved_model_settings_collection(get_selected_org_id())

    result = run_queries.query(req, feature, thread_id, saved_model_settings, space, spaces)

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


def get_organisation_settings() -> dict:  # noqa: D103
    current_org_id = get_selected_org_id()
    if not current_org_id:
        raise ValueError("Selected Org ID cannot be none.")
    result = manage_settings.get_organisation_settings(org_id=current_org_id)
    if not isinstance(result, dict):
        raise ValueError("Organisation settings has to be a dict.")
    return result


def handle_get_system_settings() -> dict[str, str]:  # noqa: D103
    result = manage_settings.get_system_settings()
    if not isinstance(result, dict):
        raise ValueError("System settings has to be a dict.")
    return result


def handle_get_selected_model_settings() -> ModelUsageSettingsCollection:
    """Handle getting the settings for the saved model."""
    current_org_id = get_selected_org_id()
    if not current_org_id:
        raise ValueError("Selected Org ID cannot be none.")
    return get_saved_model_settings_collection(current_org_id)


def get_enabled_org_features() -> list[domain.FeatureKey]:  # noqa: D103
    current_org_id = get_selected_org_id()
    if not current_org_id:
        raise ValueError("Selected Org ID cannot be none.")
    result = manage_settings.get_organisation_settings(
        org_id=current_org_id, key=config.OrganisationSettingsKey.ENABLED_FEATURES
    )
    if not isinstance(result, list):
        raise ValueError("Enabled features has to be a list of domain.FeatueKey.")
    return result

def get_enabled_system_features() -> list[domain.FeatureKey]:  # noqa: D103
    result = manage_settings.get_system_settings(
        key=config.SystemSettingsKey.ENABLED_FEATURES
    )
    if not isinstance(result, list):
        raise ValueError("Enabled features has to be a list of domain.FeatueKey.")
    return result

@tracer.start_as_current_span("handle_update_system_settings")
def handle_update_system_settings() -> None:  # noqa: D103
    manage_settings.update_system_settings(
        {
            config.SystemSettingsKey.ENABLED_FEATURES.name: [
                f.name for f in st.session_state[f"system_settings_{config.SystemSettingsKey.ENABLED_FEATURES.name}"]
            ],
        },
    )
    set_settings_session(
        {
            config.SystemSettingsKey.ENABLED_FEATURES.name: [
                f.name for f in st.session_state[f"system_settings_{config.SystemSettingsKey.ENABLED_FEATURES.name}"]
            ],
        },
        SessionKeyNameForSettings.SYSTEM,
    )


def handle_update_organisation_settings() -> None:  # noqa: D103
    current_org_id = get_selected_org_id()
    if not current_org_id:
        raise ValueError("Selected Org ID cannot be none.")
    manage_settings.update_organisation_settings(
        {
            config.OrganisationSettingsKey.ENABLED_FEATURES.name: [
                f.name for f in st.session_state[f"org_settings_{config.OrganisationSettingsKey.ENABLED_FEATURES.name}"]
            ],
            config.OrganisationSettingsKey.MODEL_COLLECTION.name: st.session_state[
                f"org_settings_default_{config.OrganisationSettingsKey.MODEL_COLLECTION.name}"
            ][0],
        },
        org_id=current_org_id,
    )
    set_settings_session(
        {
            config.OrganisationSettingsKey.ENABLED_FEATURES.name: [
                f.name for f in st.session_state[f"org_settings_{config.OrganisationSettingsKey.ENABLED_FEATURES.name}"]
            ],
        },
        SessionKeyNameForSettings.ORG,
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
