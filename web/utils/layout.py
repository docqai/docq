"""Layout components for the web app."""


import logging as log
from typing import List

import streamlit as st
from docq.config import FeatureType, LogType
from docq.domain import ConfigKey, FeatureKey, SpaceKey
from docq.manage_spaces import get_space_data_source
from st_pages import hide_pages

from .constants import ALLOWED_DOC_EXTS, SessionKeyNameForAuth, SessionKeyNameForChat
from .formatters import format_datetime, format_filesize
from .handlers import (
    get_enabled_features,
    get_max_number_of_documents,
    get_shared_space,
    get_system_settings,
    handle_chat_input,
    handle_create_space,
    handle_create_user,
    handle_delete_all_documents,
    handle_delete_document,
    handle_list_documents,
    handle_login,
    handle_logout,
    handle_reindex_space,
    handle_update_space,
    handle_update_system_settings,
    handle_update_user,
    handle_upload_file,
    list_shared_spaces,
    list_space_data_source_choices,
    list_users,
    prepare_for_chat,
    query_chat_history,
)
from .sessions import get_auth_session, get_chat_session


def production_layout() -> None:
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
    hide_pages(["Admin", "Admin_Overview", "Admin_Users", "Admin_Docs", "Admin_Logs"])


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
        f"You're logged in as `{get_auth_session()[SessionKeyNameForAuth.NAME.value]}`. Please login as a different user with correct permissions to try again."
    )
    st.stop()


def public_access() -> None:
    # __no_staff_menu()
    __no_admin_menu()


def auth_required(show_login_form: bool = True, requiring_admin: bool = False, show_logout_button: bool = True) -> bool:
    auth = get_auth_session()
    if auth:
        if show_logout_button:
            __logout_button()

        if not auth.get(SessionKeyNameForAuth.ADMIN.value, False):
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
    feats = get_enabled_features()
    # Note that we are checking `feats` first and then using `not in` here because we want to allow the features to be enabled by default.
    if feats and feature.value not in feats:
        st.error("This feature is not enabled.")
        st.info("Please contact your administrator to enable this feature.")
        st.stop()
        return False
    return True


def create_user_ui() -> None:
    with st.empty().form(key="create_user"):
        st.text_input("Username", value="", key="create_user_username")
        st.text_input("Password", value="", key="create_user_password", type="password")
        st.text_input("Full Name", value="", key="create_user_fullname")
        st.checkbox("Is Admin", value=False, key="create_user_admin")
        st.form_submit_button("Create User", on_click=handle_create_user)


def list_users_ui(username_match: str = None) -> None:
    users = list_users(username_match)
    if users:
        for id_, username, fullname, admin, archived, created_at, updated_at in users:
            is_admin = bool(admin)
            is_archived = bool(archived)
            is_current_user = id_ == get_auth_session()[SessionKeyNameForAuth.ID.value]
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
                key=f"chat_spaces_{feature.value()}",
            )
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
    st.button("Reindex", key=f"reindex_{space.value()}", on_click=handle_reindex_space, args=(space,))
    st.markdown(f"**Document Count**: {len(documents)}")

    show_upload = ds_type == "MANUAL_UPLOAD"
    show_delete = ds_type == "MANUAL_UPLOAD"

    if show_upload:
        _render_document_upload(space, documents)

    if documents:
        st.divider()
        for i, (filename, time, size) in enumerate(documents):
            with st.expander(filename):
                st.markdown(f"Size: {format_filesize(size)} | Last Modified: {format_datetime(time)}")

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


def chat_settings_ui(feature: FeatureKey) -> None:
    st.info("Settings for general chat are coming soon.")


def system_settings_ui() -> None:
    settings = get_system_settings()
    with st.form(key="system_settings"):
        st.multiselect(
            "Select the features you want to enable",
            options=[f.value for f in FeatureType],
            default=settings["enabled_features"] if settings else [f.value for f in FeatureType],
            key="system_settings_enabled_features",
        )
        st.form_submit_button(label="Save", on_click=handle_update_system_settings)


def _render_space_data_source_config_input_fields(
    data_sources: dict[str, List[ConfigKey]], prefix: str, configs: dict = None
) -> None:
    config_keys = data_sources[st.session_state[prefix + "ds_type"]]

    for key in config_keys:
        input_type = "password" if key.is_secret else "default"
        st.text_input(
            key.name,
            value=configs.get(key.key) if configs else "",
            key=prefix + "ds_config_" + key.key,
            type=input_type,
            help=key.ref_link,
            autocomplete="off",  # disable autofill by password manager etc.
        )


def create_space_ui() -> None:
    data_sources = list_space_data_source_choices()
    with st.expander("### + New Space"):
        st.text_input("Name", value="", key="create_space_name")
        st.text_input("Summary", value="", key="create_space_summary")
        ds = st.selectbox(
            "Data Source",
            options=data_sources.keys(),
            key="create_space_ds_type",
        )
        if ds:
            _render_space_data_source_config_input_fields(data_sources, "create_space_")
        st.button("Create Space", on_click=handle_create_space)


def list_spaces_ui(admin_access: bool = False) -> None:
    spaces = list_shared_spaces()
    data_sources = list_space_data_source_choices()
    if spaces:
        for id_, name, summary, archived, ds_type, ds_configs, created_at, updated_at in spaces:
            if archived and not admin_access:
                continue
            with st.expander(f"{'~~' if archived else ''}{name}{'~~' if archived else ''}"):
                st.write(f"_{summary}_")
                st.write(f"Type: **{ds_type}**")
                st.write(f"Created At: {format_datetime(created_at)} | Updated At: {format_datetime(updated_at)}")
                if admin_access:
                    st.markdown(f"ID: **{id_}** | [Manage Documents](./Admin_Docs?sid={id_})")
                    if st.button("Edit", key=f"update_space_{id_}_button"):
                        with st.form(key=f"update_space_{id_}"):
                            st.text_input("Name", value=name, key=f"update_space_{id_}_name")
                            st.text_input("Summary", value=summary, key=f"update_space_{id_}_summary")
                            st.checkbox("Is Archived", value=archived, key=f"update_space_{id_}_archived")
                            st.text_input("Type", value=ds_type, key=f"update_space_{id_}_ds_type", disabled=True)
                            _render_space_data_source_config_input_fields(
                                data_sources, f"update_space_{id_}_", ds_configs
                            )
                            st.form_submit_button("Save", on_click=handle_update_space, args=(id_,))


def show_space_details_ui(space: SpaceKey) -> None:
    (id_, name, summary, archived, ds_type, ds_configs, created_at, updated_at) = get_shared_space(space.id_)
    st.write(f"{'~~' if archived else ''}{name}{'~~' if archived else ''}")
    st.write(f"ID: **{id_}**")
    st.write(f"Summary: _{summary}_")
    st.write(f"Type: **{ds_type}**")
    st.write(f"Created At: {format_datetime(created_at)} | Updated At: {format_datetime(updated_at)}")


def list_logs_ui(type_: LogType) -> None:
    st.info("Logs are coming soon.")
