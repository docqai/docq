"""Layout components for the web app."""


import logging as log
from typing import List, Tuple

import streamlit as st
from docq.access_control.main import SpaceAccessType
from docq.config import FeatureType, LogType, SystemSettingsKey
from docq.domain import FeatureKey, SpaceKey
from st_pages import hide_pages
from streamlit.delta_generator import DeltaGenerator

from .constants import ALLOWED_DOC_EXTS, SessionKeyNameForAuth, SessionKeyNameForChat
from .formatters import format_archived, format_datetime, format_filesize, format_timestamp
from .handlers import (
    get_enabled_features,
    get_max_number_of_documents,
    get_shared_space,
    get_shared_space_permissions,
    get_space_data_source,
    get_space_data_source_choice_by_type,
    get_system_settings,
    handle_auto_login,
    handle_chat_input,
    handle_create_space,
    handle_create_space_group,
    handle_create_user,
    handle_create_user_group,
    handle_delete_all_documents,
    handle_delete_document,
    handle_delete_space_group,
    handle_delete_user_group,
    handle_list_documents,
    handle_login,
    handle_logout,
    handle_manage_space_permissions,
    handle_reindex_space,
    handle_update_space_details,
    handle_update_space_group,
    handle_update_system_settings,
    handle_update_user,
    handle_update_user_group,
    handle_upload_file,
    list_shared_spaces,
    list_space_data_source_choices,
    list_space_groups,
    list_user_groups,
    list_users,
    prepare_for_chat,
    query_chat_history,
)
from .sessions import get_auth_session, get_chat_session


def production_layout() -> None:
    """Layout for the production environment."""
    hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
        """
    st.markdown(hide_menu_style, unsafe_allow_html=True)


def __no_staff_menu() -> None:
    hide_pages(
        [
            "Your_Space",
            "General_Chat",
            "Ask_Your_Documents",
            "Manage_Your_Document",
            "Shared_Spaces",
            "Ask_Shared_Documents",
            "List_Shared_Spaces",
        ]
    )


def __no_admin_menu() -> None:
    hide_pages(
        [
            "Admin",
            "Admin_Settings",
            "Admin_Spaces",
            "Admin_Space_Groups",
            "Admin_Docs",
            "Admin_Users",
            "Admin_User_Groups",
            "Admin_Logs",
        ]
    )


def __login_form() -> None:
    __no_admin_menu()
    st.markdown("### Please login to continue")
    username = st.text_input("Username", value="", key="login_username")
    password = st.text_input("Password", value="", key="login_password", type="password")
    if st.button("Login"):
        if handle_login(username, password):
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")
            st.stop()
    else:
        st.stop()


def __logout_button() -> None:
    if st.button("Logout"):
        handle_logout()
        st.experimental_rerun()


def __not_authorised() -> None:
    st.error("You are not authorized to access this page.")
    st.info(
        f"You're logged in as `{get_auth_session()[SessionKeyNameForAuth.NAME.name]}`. Please login as a different user with correct permissions to try again."
    )
    st.stop()


def public_access() -> None:
    """Menu options for public access."""
    # __no_staff_menu()
    __no_admin_menu()

@handle_auto_login
def auth_required(show_login_form: bool = True, requiring_admin: bool = False, show_logout_button: bool = True) -> bool:
    """Decide layout based on current user's access."""
    auth = get_auth_session()
    if auth:
        if show_logout_button:
            __logout_button()

        if not auth.get(SessionKeyNameForAuth.ADMIN.name, False):
            __no_admin_menu()
            if requiring_admin:
                __not_authorised()
                return False

        return True
    else:
        if show_login_form:
            __login_form()
        return False


def feature_enabled(feature: FeatureKey) -> bool:
    """Check if a feature is enabled."""
    feats = get_enabled_features()
    # Note that we are checking `feats` first and then using `not in` here because we want to allow the features to be enabled by default.
    if feats and feature.name not in feats:
        st.error("This feature is not enabled.")
        st.info("Please contact your administrator to enable this feature.")
        st.stop()
        return False
    return True


def create_user_ui() -> None:
    """Create a new user."""
    with st.expander("### + New User"), st.form(key="create_user"):
        st.text_input("Username", value="", key="create_user_username")
        st.text_input("Password", value="", key="create_user_password", type="password")
        st.text_input("Full Name", value="", key="create_user_fullname")
        st.checkbox("Is Admin", value=False, key="create_user_admin")
        st.form_submit_button("Create User", on_click=handle_create_user)


def list_users_ui(username_match: str = None) -> None:
    """List all users."""
    users = list_users(username_match)
    if users:
        for id_, username, fullname, admin, archived, created_at, updated_at in users:
            is_admin = bool(admin)
            is_archived = bool(archived)
            is_current_user = id_ == get_auth_session()[SessionKeyNameForAuth.ID.name]
            with st.expander(
                f"{'~~' if is_archived else ''}{username} ({fullname}){'~~' if is_archived else ''} {'(You)' if is_current_user else ''}"
            ):
                st.markdown(f"ID: **{id_}** | Admin: **{is_admin}**")
                st.write(f"Created At: {format_datetime(created_at)} | Updated At: {format_datetime(updated_at)}")
                if st.button("Edit", key=f"update_user_{id_}_button"):
                    with st.form(key=f"update_user_{id_}"):
                        st.text_input("Username", value=username, key=f"update_user_{id_}_username")
                        st.text_input("Password", type="password", key=f"update_user_{id_}_password")
                        st.text_input("Full Name", value=fullname, key=f"update_user_{id_}_fullname")
                        st.checkbox("Is Admin", value=is_admin, key=f"update_user_{id_}_admin")
                        st.checkbox("Is Archived", value=is_archived, key=f"update_user_{id_}_archived")
                        st.form_submit_button("Save", on_click=handle_update_user, args=(id_,))


def create_user_group_ui() -> None:
    """Create a new group."""
    with st.expander("### + New User Group"), st.form(key="create_user_group"):
        st.text_input("Name", value="", key="create_user_group_name")
        st.form_submit_button("Create User Group", on_click=handle_create_user_group)


def list_user_groups_ui(name_match: str = None) -> None:
    """List all groups."""
    groups = list_user_groups(name_match)
    if groups:
        for id_, name, members, created_at, updated_at in groups:
            with st.expander(f"{name} ({len(members)} members)"):
                st.write(f"ID: **{id_}**")
                st.write(f"Created At: {format_datetime(created_at)} | Updated At: {format_datetime(updated_at)}")
                edit_col, delete_col = st.columns(2)
                with edit_col:
                    if st.button("Edit", key=f"update_user_group_{id_}_button"):
                        with st.form(key=f"update_user_group_{id_}"):
                            st.text_input("Name", value=name, key=f"update_user_group_{id_}_name")
                            st.multiselect(
                                "Members",
                                options=[(x[0], x[2]) for x in list_users()],
                                default=members,
                                key=f"update_user_group_{id_}_members",
                                format_func=lambda x: x[1],
                            )
                            st.form_submit_button("Save", on_click=handle_update_user_group, args=(id_,))
                with delete_col:
                    if st.button("Delete", key=f"delete_user_group_{id_}_button"):
                        with st.form(key=f"delete_user_group_{id_}"):
                            st.warning("Are you sure you want to delete this group?")
                            st.form_submit_button("Confirm", on_click=handle_delete_user_group, args=(id_,))


def create_space_group_ui() -> None:
    """Create a new space group."""
    with st.expander("### + New Space Group"), st.form(key="create_space_group"):
        st.text_input("Name", value="", key="create_space_group_name")
        st.text_input("Summary", value="", key="create_space_group_summary")
        st.form_submit_button("Create Space Group", on_click=handle_create_space_group)


def list_space_groups_ui(name_match: str = None) -> None:
    """List all space groups."""
    groups = list_space_groups(name_match)
    if groups:
        for id_, name, summary, members, created_at, updated_at in groups:
            with st.expander(f"{name} ({len(members)} spaces)"):
                st.write(f"ID: **{id_}**")
                st.write(f"Summary: _{summary}_")
                st.write(f"Created At: {format_datetime(created_at)} | Updated At: {format_datetime(updated_at)}")
                edit_col, delete_col = st.columns(2)
                with edit_col:
                    if st.button("Edit", key=f"update_space_group_{id_}_button"):
                        with st.form(key=f"update_space_group_{id_}"):
                            st.text_input("Name", value=name, key=f"update_space_group_{id_}_name")
                            st.text_input("Summary", value=summary, key=f"update_space_group_{id_}_summary")
                            st.multiselect(
                                "Spaces",
                                options=[(x[0], x[1]) for x in list_shared_spaces()],
                                default=members,
                                key=f"update_space_group_{id_}_members",
                                format_func=lambda x: x[1],
                            )
                            st.form_submit_button("Save", on_click=handle_update_space_group, args=(id_,))
                with delete_col:
                    if st.button("Delete", key=f"delete_space_group_{id_}_button"):
                        with st.form(key=f"delete_space_group_{id_}"):
                            st.warning("Are you sure you want to delete this group?")
                            st.form_submit_button("Confirm", on_click=handle_delete_space_group, args=(id_,))


def _chat_message(message_: str, is_user: bool) -> None:
    if is_user:
        with st.chat_message("user"):
            st.write(message_)
    else:
        with st.chat_message("assistant"):
            st.markdown(message_, unsafe_allow_html=True)


def chat_ui(feature: FeatureKey) -> None:
    """Chat UI layout."""
    prepare_for_chat(feature)
    with st.container():
        if feature.type_ == FeatureType.ASK_SHARED:
            spaces = list_shared_spaces()
            st.multiselect(
                "Including these shared spaces:",
                options=spaces,
                default=spaces,
                format_func=lambda x: x[1],
                key=f"chat_shared_spaces_{feature.value()}",
            )
            st.checkbox("Including your documents", value=True, key="chat_personal_space")
            st.divider()
        if st.button("Load chat history earlier"):
            query_chat_history(feature)
        day = format_datetime(get_chat_session(feature.type_, SessionKeyNameForChat.CUTOFF))
        st.markdown(f"#### {day}")
        for _, text, is_user, time in get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY):
            if format_datetime(time) != day:
                day = format_datetime(time)
                st.markdown(f"#### {day}")
            _chat_message(text, is_user)

    # st.divider()
    st.chat_input(
        "Type your question here",
        key=f"chat_input_{feature.value()}",
        on_submit=handle_chat_input,
        args=(feature,),
    )


def _render_document_upload(space: SpaceKey, documents: List) -> None:
    max_size = get_max_number_of_documents(space.type_)
    if len(documents) < max_size:
        with st.form("Upload", clear_on_submit=True):
            st.file_uploader(
                "Upload your documents here",
                type=ALLOWED_DOC_EXTS,
                key=f"uploaded_file_{space.value()}",
                accept_multiple_files=True,
            )
            st.form_submit_button(label="Upload", on_click=handle_upload_file, args=(space,))
    else:
        st.warning(f"You cannot upload more than {max_size} documents.")


def documents_ui(space: SpaceKey) -> None:
    """Displays the UI for managing documents in a space."""
    documents = handle_list_documents(space)
    (ds_type, _) = get_space_data_source(space)

    show_upload = ds_type == "MANUAL_UPLOAD"
    show_delete = ds_type == "MANUAL_UPLOAD"
    show_reindex = True

    if show_upload:
        _render_document_upload(space, documents)

    if show_reindex:
        st.button("Reindex", key=f"reindex_{space.value()}_top", on_click=handle_reindex_space, args=(space,))

    if documents:
        st.divider()
        st.markdown(f"**Document Count**: {len(documents)}")
        for i, (filename, time, size) in enumerate(documents):
            with st.expander(filename):
                st.markdown(f"Size: {format_filesize(size)} | Last Modified: {format_timestamp(time)}")

                if show_delete:
                    st.button(
                        "Delete",
                        key=f"delete_file_{i}_{space.value()}",
                        on_click=handle_delete_document,
                        args=(
                            filename,
                            space,
                        ),
                    )

        if show_delete:
            st.button(
                "Delete all documents",
                key=f"delete_all_files_{space.value()}",
                on_click=handle_delete_all_documents,
                args=(space,),
            )
    else:
        st.info("No documents or the space does not support listing documents.")


def chat_settings_ui(feature: FeatureKey) -> None:
    """Chat settings."""
    st.info("Settings for general chat are coming soon.")


def system_settings_ui() -> None:
    """System settings."""
    settings = get_system_settings()
    with st.form(key="system_settings"):
        st.multiselect(
            SystemSettingsKey.ENABLED_FEATURES.value,
            options=[f for f in FeatureType],
            format_func=lambda x: x.value,
            default=[FeatureType.__members__[k] for k in settings[SystemSettingsKey.ENABLED_FEATURES.name]]
            if settings
            else [f for f in FeatureType],
            key=f"system_settings_{SystemSettingsKey.ENABLED_FEATURES.name}",
        )
        st.form_submit_button(label="Save", on_click=handle_update_system_settings)


def _render_space_data_source_config_input_fields(data_source: Tuple, prefix: str, configs: dict = None) -> None:
    for key in data_source[2]:
        input_type = "password" if key.is_secret else "default"
        st.text_input(
            f"{key.name}{'' if key.is_optional else ' *'}",
            value=configs.get(key.key) if configs else "",
            key=prefix + "ds_config_" + key.key,
            type=input_type,
            help=key.ref_link,
            autocomplete="off",  # disable autofill by password manager etc.
        )


def create_space_ui() -> None:
    """Create a new space."""
    data_sources = list_space_data_source_choices()
    with st.expander("### + New Space"):
        st.text_input("Name", value="", key="create_space_name")
        st.text_input("Summary", value="", key="create_space_summary")
        ds = st.selectbox(
            "Data Source",
            options=data_sources,
            key="create_space_ds_type",
            format_func=lambda x: x[1],
        )
        if ds:
            _render_space_data_source_config_input_fields(ds, "create_space_")
        st.button("Create Space", on_click=handle_create_space)


def _render_view_space_details_with_container(
    space_data: Tuple, data_source: Tuple, use_expander: bool = False
) -> DeltaGenerator:
    id_, name, summary, archived, ds_type, ds_configs, created_at, updated_at = space_data
    container = st.expander(format_archived(name, archived)) if use_expander else st.container()
    with container:
        if not use_expander:
            st.write(format_archived(name, archived))
        st.write(f"ID: **{id_}**")
        st.write(f"Summary: _{summary}_")
        st.write(f"Type: **{data_source[1]}**")
        st.write(f"Created At: {format_datetime(created_at)} | Updated At: {format_datetime(updated_at)}")
    return container


def _render_edit_space_details(space_data: Tuple, data_source: Tuple) -> None:
    id_, name, summary, archived, ds_type, ds_configs, _, _ = space_data

    if st.button("Edit", key=f"update_space_{id_}_button"):
        with st.form(key=f"update_space_details_{id_}"):
            st.text_input("Name", value=name, key=f"update_space_details_{id_}_name")
            st.text_input("Summary", value=summary, key=f"update_space_details_{id_}_summary")
            st.checkbox("Is Archived", value=archived, key=f"update_space_details_{id_}_archived")
            st.selectbox(
                "Data Source",
                options=[data_source],
                index=0,
                key=f"update_space_details_{id_}_ds_type",
                disabled=True,
                format_func=lambda x: x[1],
            )
            _render_space_data_source_config_input_fields(data_source, f"update_space_details_{id_}_", ds_configs)
            st.form_submit_button("Save", on_click=handle_update_space_details, args=(id_,))


def _render_manage_space_permissions(space_data: Tuple) -> None:
    id_, *_ = space_data
    permissions = get_shared_space_permissions(id_)

    if st.button("Permissions", key=f"manage_space_permissions_{id_}_button"):
        with st.form(key=f"manage_space_permissions_{id_}"):
            st.checkbox(
                "Public Access",
                value=permissions[SpaceAccessType.PUBLIC],
                key=f"manage_space_permissions_{id_}_{SpaceAccessType.PUBLIC.name}",
            )
            st.multiselect(
                "Users",
                options=[(u[0], u[1]) for u in list_users()],
                default=permissions[SpaceAccessType.USER],
                key=f"manage_space_permissions_{id_}_{SpaceAccessType.USER.name}",
                format_func=lambda x: x[1],
            )
            st.multiselect(
                "Groups",
                options=[(g[0], g[1]) for g in list_user_groups()],
                default=permissions[SpaceAccessType.GROUP],
                key=f"manage_space_permissions_{id_}_{SpaceAccessType.GROUP.name}",
                format_func=lambda x: x[1],
            )
            st.form_submit_button("Save", on_click=handle_manage_space_permissions, args=(id_,))


def list_spaces_ui(admin_access: bool = False) -> None:
    """List all spaces."""
    spaces = list_shared_spaces()
    if spaces:
        for s in spaces:
            if s[3] and not admin_access:
                continue
            ds = get_space_data_source_choice_by_type(s[4])
            container = _render_view_space_details_with_container(s, ds, True)
            if admin_access:
                with container:
                    st.markdown(f"[Manage Documents](./Admin_Docs?sid={s[0]})")
                    col_details, col_permissions = st.columns(2)
                    with col_details:
                        _render_edit_space_details(s, ds)
                    with col_permissions:
                        _render_manage_space_permissions(s)


def show_space_details_ui(space: SpaceKey) -> None:
    """Show details of a space."""
    s = get_shared_space(space.id_)
    ds = get_space_data_source_choice_by_type(s[4])
    _render_view_space_details_with_container(s, ds)


def list_logs_ui(type_: LogType) -> None:
    """List logs per log type."""
    st.info("Logs are coming soon.")
