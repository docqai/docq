"""Layout components for the web app."""
import base64
import logging as log
import random
import re
from typing import Any, Callable, List, Optional, Tuple
from urllib.parse import quote_plus, unquote_plus

import docq
import streamlit as st
from docq import services, setup
from docq.access_control.main import SpaceAccessType
from docq.config import FeatureType, LogType, SpaceType, SystemSettingsKey
from docq.data_source.main import FileStorageServiceHandlers, FileStorageServiceKeys, SetFSHandler
from docq.domain import ConfigKey, DocumentListItem, FeatureKey, SpaceKey
from docq.model_selection.main import (
    ModelUsageSettingsCollection,
    get_model_settings_collection,
    list_available_model_settings_collections,
)
from docq.support.auth_utils import (
    get_cache_auth_session,
    reset_cache_and_cookie_auth_session,
    verify_cookie_hmac_session_id,
)
from st_pages import hide_pages
from streamlit.components.v1 import html
from streamlit.delta_generator import DeltaGenerator

from .constants import ALLOWED_DOC_EXTS, SessionKeyNameForAuth, SessionKeyNameForChat
from .error_ui import _handle_error_state_ui
from .formatters import format_archived, format_datetime, format_filesize, format_timestamp
from .handlers import (
    _set_session_state_configs,
    get_enabled_features,
    get_max_number_of_documents,
    get_shared_space,
    get_shared_space_permissions,
    get_space_data_source,
    get_space_data_source_choice_by_type,
    get_system_settings,
    handle_archive_org,
    handle_chat_input,
    handle_check_account_activated,
    handle_check_mailer_ready,
    handle_check_user_exists,
    handle_create_new_chat,
    handle_create_org,
    handle_create_space,
    handle_create_space_group,
    handle_create_user,
    handle_create_user_group,
    handle_delete_all_documents,
    handle_delete_document,
    handle_delete_space_group,
    handle_delete_user_group,
    handle_get_gdrive_authurl,
    handle_get_gravatar_url,
    handle_list_documents,
    handle_list_orgs,
    handle_login,
    handle_logout,
    handle_manage_space_permissions,
    handle_org_selection_change,
    handle_public_session,
    handle_redirect_to_url,
    handle_reindex_space,
    handle_resend_email_verification,
    handle_update_org,
    handle_update_space_details,
    handle_update_space_group,
    handle_update_system_settings,
    handle_update_user,
    handle_update_user_group,
    handle_upload_file,
    handle_user_signup,
    handle_verify_email,
    list_public_spaces,
    list_shared_spaces,
    list_space_data_source_choices,
    list_space_groups,
    list_user_groups,
    list_users,
    list_users_by_current_org,
    prepare_for_chat,
    query_chat_history,
)
from .sessions import (
    get_auth_session,
    get_authenticated_user_id,
    get_chat_session,
    get_public_session_id,
    get_public_space_group_id,
    get_selected_org_id,
    is_current_user_super_admin,
    reset_session_state,
    session_state_exists,
)

_chat_ui_script = """
<script>
    parent = window.parent.document || window.document
    const [themeKey, themeKey1] = ['stActiveTheme-/Ask_Shared_Documents-v1', 'stActiveTheme-/-v1']
    const activeTheme = localStorage.getItem('stActiveTheme-/Ask_Shared_Documents-v1') || localStorage.getItem('stActiveTheme-/-v1')
    const theme = JSON.parse(activeTheme)
    const spaceSelector = parent.getElementsByClassName('streamlit-expander')[0]
    const spaceSelectorPresent = spaceSelector && spaceSelector.parentNode && spaceSelector.parentNode.parentNode

    const setTheme = (theme) => {
        localStorage.setItem(themeKey, JSON.stringify(theme))
        localStorage.setItem(themeKey1, JSON.stringify(theme))
    }

    /* Space Selector. */

    const resizeSelector = (spaceSelector) => {
        if (spaceSelectorPresent && spaceSelector) {
            const _parent = spaceSelector.parentNode.parentNode
            const _container = spaceSelector.parentNode
            const parentWidth = _parent.offsetWidth
            _container.setAttribute('style', `width: ${parentWidth}px;`)
        }
    };

    const formatSpaceSelector = (theme = null) => {
        resizeSelector(spaceSelector)

        // Set background color to the space selector based on active theme.
        if (theme && theme === 'Light' && spaceSelector) {
            spaceSelector.setAttribute('style', 'background-color: #fff;');
        } else if (theme && theme === 'Dark' && spaceSelector) {
            spaceSelector.setAttribute('style', 'background-color: #1f1f1f;');
        } else if (spaceSelector) {
            // Default to browsers theme preference if no theme is set.
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                setTheme({name: 'Dark'})
                spaceSelector.setAttribute('style', 'background-color: #1f1f1f;');
            } else {
                setTheme({name: 'Light'})
                spaceSelector.setAttribute('style', 'background-color: #fff;');
            }
        }
    }

    formatSpaceSelector(theme?.name)

    /* Gravatar */
    const all = parent.querySelectorAll('[alt="user avatar"]')

    // Open users gravatar profile in new tab.
    all.forEach((el) => {
        el.addEventListener('click', () => {
            const email = el.getAttribute('src').split('?')[0].split('/').slice(-1)[0]
            if (email) {
                window.open(`https://www.gravatar.com/${email}`, '_blank')
            } else {
                window.open('https://www.gravatar.com/', '_blank')
            }
    })})

    // Update space selector theme automatically on theme change
    window.onstorage = (e) => {
        if (e.key === 'stActiveTheme-/Ask_Shared_Documents-v1' || e.key === 'stActiveTheme-/-v1') {
            const activeTheme = localStorage.getItem('stActiveTheme-/Ask_Shared_Documents-v1') || localStorage.getItem('stActiveTheme-/-v1')
            const theme = JSON.parse(activeTheme)
            formatSpaceSelector(theme.name)
        }
    }

    // Format Logout button and listen for resize event.
    if (spaceSelectorPresent) {
      const logoutBtn = parent.querySelectorAll('button[kind="secondary"]')[0]
      logoutBtn.setAttribute('style', 'margin-top: 1rem !important;');
      const resizeObserver = new ResizeObserver(() => resizeSelector(spaceSelector))
      resizeObserver.observe(spaceSelector.parentNode.parentNode)
    }

</script>
"""


def chat_ui_script() -> None:
    """A javascript snippet that runs on the chat UI."""
    st.write("<style> iframe {min-height: 0; height: 0}</style>", unsafe_allow_html=True)
    html(_chat_ui_script)


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


def __embed_page_config() -> None:
    st.markdown(
        """
        <style>
            [data-testid="collapsedControl"] {
                display: none !important;
            }
            section[data-testid="stSidebar"] {
                display: none !important;
            }
            .block-container {
                padding-top: 1rem !important;
            }
            .stChatFloatingInputContainer {
                padding-bottom: 3rem !important;
            }
            div.element-container:has(.stAlert) {
                padding-top: 2rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def __always_hidden_pages() -> None:
    """These pages are always hidden whether the user is an admin or not."""
    hide_pages(["widget", "signup", "verify"])


def configure_top_right_menu() -> None:
    """Configure the Streamlit top right menu."""
    st.set_page_config(menu_items={"About": f"**{docq.__summary__}** \
                                Version: **{docq.__version__}** | \
                                Homepage: {docq.__homepage_url__} | \
                                Docs: {docq.__documentation_url__} \
                                Twitter: https://twitter.com/docqai \
                               "})


def __resend_verification_ui(username: str, form: str,  ) -> None:
    """Resend email verification UI."""
    msg = st.empty()
    msg.error("Your account is not activated. Please check your email for the activation link.")
    _, center, _ = st.columns([1, 1, 1])
    if handle_check_mailer_ready() and center.button("Resend verification email"):
        handle_resend_email_verification(username)
        st.session_state[f"{form}-resend-verification-email"] = False
        msg.success("Verification email sent. Please check your email.")
    st.stop()


def __login_form() -> None:
    __no_admin_menu()
    st.markdown('Dont have an account? signup <a href="/signup" target="_self">here</a>', unsafe_allow_html=True)
    st.markdown("### Please login to continue")
    form_validator, form_name = st.empty(), "login-form"
    username = st.text_input("Username", value="", key="login_username")
    password = st.text_input("Password", value="", key="login_password", type="password")
    if st.button("Login"):
        if handle_login(username, password):
            st.experimental_rerun()
        elif not handle_check_account_activated(username):
            st.session_state[f"{form_name}-resend-verification-email"] = True
        else:
            form_validator.error("The Username or the Password you've entered doesn't match what we have.")
            st.stop()

    if st.session_state.get(f"{form_name}-resend-verification-email", False):
        with form_validator.container():
            __resend_verification_ui(username, form_name)
    else:
        st.stop()


def __logout_button() -> None:
    sidebar = st.sidebar
    if sidebar.button("Logout"):
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
    __always_hidden_pages()


def auth_required(show_login_form: bool = True, requiring_admin: bool = False, show_logout_button: bool = True) -> bool:
    """Decide layout based on current user's access."""
    log.debug("auth_required() called")
    auth = None
    __always_hidden_pages()

    session_state_existed = session_state_exists()
    log.debug("auth_required(): session_state_existed: %s", session_state_existed)
    if session_state_existed:
        auth = get_auth_session()
    elif verify_cookie_hmac_session_id() is not None:
        # there's a valid auth session token. Let's get session state from cache.
        auth = get_cache_auth_session()
        log.debug("auth_required(): Got auth session state from cache: %s", auth)

    if auth:
        log.debug("auth_required(): Valid auth session found: %s", auth)
        if not session_state_existed:
            # the user probably refreshed the page resetting Streamlit session state because it's bound to a browser session connection.
            _set_session_state_configs(
                user_id=auth[SessionKeyNameForAuth.ID.name],
                selected_org_id=auth[SessionKeyNameForAuth.SELECTED_ORG_ID.name],
                name=auth[SessionKeyNameForAuth.NAME.name],
                username=auth[SessionKeyNameForAuth.USERNAME.name],
                anonymous=False,
                super_admin=auth[SessionKeyNameForAuth.SUPER_ADMIN.name],
                selected_org_admin=auth[SessionKeyNameForAuth.SELECTED_ORG_ADMIN.name],
            )

        if show_logout_button:
            __logout_button()

        if not auth.get(SessionKeyNameForAuth.SELECTED_ORG_ADMIN.name, False):
            __no_admin_menu()
            if requiring_admin:
                __not_authorised()
                return False

        return True
    else:
        log.debug("auth_required(): No valid auth session found. User needs to re-authenticate.")
        reset_session_state()
        reset_cache_and_cookie_auth_session()
        if show_login_form:
            __login_form()
        return False


def public_session_setup() -> None:
    """Initialize session state for the public pages."""
    handle_public_session()


def feature_enabled(feature: FeatureType) -> bool:
    """Check if a feature is enabled."""
    feats = get_enabled_features()
    # Note that we are checking `feats` first and then using `not in` here because we want to allow the features to be enabled by default.
    if feats and feature.name not in feats:
        st.error("This feature is not enabled.")
        st.info("Please contact your administrator to enable this feature.")
        st.stop()
        return False
    return True


def public_space_enabled(feature: FeatureType) -> None:
    """Check if public space is ready."""
    __embed_page_config()
    feature_enabled(feature)
    space_group_id = get_public_space_group_id()
    session_id = get_public_session_id()
    feature_is_ready, spaces = (space_group_id != -1 or session_id != -1), None
    if feature_is_ready:
        spaces = list_public_spaces()
    if not feature_is_ready or not spaces:  # Stop the app if there are no public spaces.
        st.error("This feature is not ready.")
        st.info("Please contact your administrator to configure this feature.")
        st.stop()


def create_user_ui() -> None:
    """Create a new user."""
    with st.expander("### + New User"), st.form(key="create_user"):
        st.text_input("Username", value="", key="create_user_username")
        st.text_input("Password", value="", key="create_user_password", type="password")
        st.text_input("Full Name", value="", key="create_user_fullname")
        st.form_submit_button("Create User", on_click=handle_create_user)
        _handle_error_state_ui(key="create_user", bubble_error_message=True)


def list_users_ui(username_match: str = None) -> None:
    """List all users."""
    users = list_users_by_current_org(username_match)

    edit_super_admin_disabled = not is_current_user_super_admin()

    if users:
        for id_, org_id, username, fullname, super_admin, org_admin, archived, created_at, updated_at in users:
            is_current_user = id_ == get_authenticated_user_id()
            with st.expander(
                f"{'~~' if archived else ''}{username} ({fullname}){'~~' if archived else ''} {'(You)' if is_current_user else ''}"
            ):
                st.markdown(f"ID: **{id_}** | Is Super Admin: **{bool(super_admin)}**")
                st.write(f"Created At: {format_datetime(created_at)} | Updated At: {format_datetime(updated_at)}")
                if st.button("Edit", key=f"update_user_{id_}_button"):
                    with st.form(key=f"update_user_{id_}"):
                        st.text_input("Username", value=username, key=f"update_user_{id_}_username")
                        st.text_input("Password", type="password", key=f"update_user_{id_}_password")
                        st.text_input("Full Name", value=fullname, key=f"update_user_{id_}_fullname")
                        st.checkbox(
                            "Is Super Admin",
                            value=super_admin,
                            key=f"update_user_{id_}_super_admin",
                            disabled=edit_super_admin_disabled,
                        )
                        st.checkbox("Is Archived", value=archived, key=f"update_user_{id_}_archived")
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
                                options=[(x[0], x[3]) for x in list_users_by_current_org()],
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


def create_org_ui() -> None:
    """Create a new organization."""
    with st.expander("### + New Organization"), st.form(key="create_org"):
        st.text_input("Name", value="", key="create_org_name")
        st.form_submit_button("Create Organization", on_click=handle_create_org)
        _handle_error_state_ui(key="create_org", bubble_error_message=True)


def list_orgs_ui(name_match: str = None) -> None:
    """List all organizations."""
    orgs = handle_list_orgs(name_match=name_match)
    current_user_id = get_authenticated_user_id()
    if orgs:
        for org_id, name, members, created_at, updated_at in orgs:
            with st.expander(f"{name}"):
                st.write(f"ID: **{org_id}**")
                st.write(f"Created At: {format_datetime(created_at)} | Updated At: {format_datetime(updated_at)}")
                edit_col, archive_col = st.columns(2)
                edit_button_disabled = True
                # only enable edit button if current user is an org admin
                log.debug("list_orgs_ui() org_id: %s, members: %s", org_id, members)
                edit_button_disabled = not (
                    any([x[0] == current_user_id and bool(x[2]) is True for x in members])
                )  # only org_admins can edit orgs.

                options = [
                    (x[0], x[2], next((y[2] for y in members if y[0] == x[0]), 0)) for x in list_users()
                ]  # map org_admin field for existing members.
                with edit_col:
                    if st.button("Edit", key=f"update_org_{org_id}_button", disabled=edit_button_disabled):
                        with st.form(key=f"update_org_{org_id}"):
                            st.text_input("Name", value=name, key=f"update_org_{org_id}_name")
                            st.multiselect(
                                "Members",
                                options=options,
                                default=members,
                                key=f"update_org_{org_id}_members",
                                format_func=lambda x: x[1],
                            )
                            st.form_submit_button("Save", on_click=handle_update_org, args=(org_id,))
                with archive_col:
                    if st.button("Archive", key=f"archive_org_{org_id}_button"):
                        with st.form(key=f"archive_org_{org_id}"):
                            st.warning("Are you sure you want to archive this organization?")
                            st.form_submit_button("Confirm", on_click=handle_archive_org, args=(org_id,))


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
        for id_, org_id, name, summary, members, created_at, updated_at in groups:
            with st.expander(f"{name} ({len(members)} spaces)"):
                st.write(f"ID: **{id_}**")
                st.write(f"Org ID: **{org_id}**")
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
                                options=[(x[0], x[2]) for x in list_shared_spaces()],
                                default=members,
                                key=f"update_space_group_{id_}_members",
                                format_func=lambda x: x[1],
                            )
                            st.form_submit_button("Save", on_click=handle_update_space_group, args=(id_,))
                with delete_col:
                    if st.button("Delete", key=f"delete_space_group_{id_}_button"):
                        with st.form(key=f"delete_space_group_{id_}"):
                            st.warning("Are you sure you want to delete this group?")
                            st.form_submit_button("Confirm", on_click=handle_delete_space_group, args=(id_))


def _chat_message(message_: str, is_user: bool) -> None:
    if is_user:
        with st.chat_message("user", avatar=handle_get_gravatar_url()):
            st.write(message_)
    else:
        with st.chat_message(
            "assistant", avatar="https://github.com/docqai/docq/blob/main/docs/assets/logo.jpg?raw=true"
        ):
            st.markdown(message_, unsafe_allow_html=True)


def _personal_ask_style() -> None:
    """Custom style for personal ask."""
    st.write(
        """
    <style>
        [data-testid="stExpander"] {
            z-index: 1000;
            position: fixed;
            top: 46px;
        }

        [data-testid="stExpander"] .row-widget.stMultiSelect label {
            display: none !important;
        }

    </style>
    """,
        unsafe_allow_html=True,
    )


def chat_ui(feature: FeatureKey) -> None:
    """Chat UI layout."""
    prepare_for_chat(feature)
    # Style for formatting sources list.
    st.write(
        """<style>
            [data-testid="stMarkdownContainer"] h6 {
                padding: 0px !important;
            }

            [data-testid="stMarkdownContainer"] h5 {
                padding: 1rem 0 0 0 !important;
            }

            [data-testid="stMarkdownContainer"] blockquote {
                margin-top: 0.5rem !important;
            }

            [alt="user avatar"], [alt="assistant avatar"] {
                border-radius: 6px;
                width: 2rem !important;
                height: 2rem !important;
                cursor: pointer;
            }

            [alt="assistant avatar"] {
                border-radius: 0;
            }

        </style>
    """,
        unsafe_allow_html=True,
    )
    with st.container():
        if feature.type_ == FeatureType.ASK_SHARED:
            _personal_ask_style()
            with st.expander("Including these shared spaces:"):
                spaces = list_shared_spaces()
                st.multiselect(
                    "Including these shared spaces:",
                    options=spaces,
                    default=spaces,
                    format_func=lambda x: x[2],
                    key=f"chat_shared_spaces_{feature.value()}",
                )
                st.checkbox("Including your documents", value=True, key="chat_personal_space")

        load_history, create_new_chat = st.columns([3, 1])
        with load_history:
            if st.button("Load chat history earlier"):
                query_chat_history(feature)
        with create_new_chat:
            if st.button("New chat"):
                handle_create_new_chat(feature)
    with st.container():
        day = format_datetime(get_chat_session(feature.type_, SessionKeyNameForChat.CUTOFF))
        st.markdown(f"#### {day}")

        for x in get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY):
            # x = (id, text, is_user, time, thread_id)
            if format_datetime(x[3]) != day:
                day = format_datetime(x[3])
                st.markdown(f"#### {day}")
            _chat_message(x[1], x[2])
        chat_ui_script()

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
    permisssion = get_shared_space_permissions(space.id_)
    if permisssion.get(SpaceAccessType.PUBLIC, False):
        st.warning("This is a public space, Do not add any sensitive information.")

    documents: List[DocumentListItem] = handle_list_documents(space)
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
        for i, document in enumerate(documents):
            with st.expander(document.link):
                st.markdown(
                    f"Size: {format_filesize(document.size)} | Last Modified: {format_timestamp(document.indexed_on)}"
                )

                if show_delete:
                    st.button(
                        "Delete",
                        key=f"delete_file_{i}_{space.value()}",
                        on_click=handle_delete_document,
                        args=(
                            document.link,
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
    log.debug("saved settings raw: %s", settings)
    with st.form(key="system_settings"):
        enabled_features_container = st.container()

        model_settings_container = st.container()

        st.form_submit_button(
            label="Save",
            on_click=handle_update_system_settings,
        )

        enabled_features_container.multiselect(
            SystemSettingsKey.ENABLED_FEATURES.value,
            options=[f for f in FeatureType],
            format_func=lambda x: x.value,
            default=[FeatureType.__members__[k] for k in settings[SystemSettingsKey.ENABLED_FEATURES.name]]
            if settings
            else [f for f in FeatureType],
            key=f"system_settings_{SystemSettingsKey.ENABLED_FEATURES.name}",
        )

        available_models = list_available_model_settings_collections()
        log.debug("available models %s", available_models)
        saved_model = (
            settings[SystemSettingsKey.MODEL_COLLECTION.name]
            if SystemSettingsKey.MODEL_COLLECTION.name in settings
            else None
        )

        log.debug("saved model: %s", saved_model)
        list_keys = list(available_models.keys())
        saved_model_index = list_keys.index(saved_model) if saved_model and list_keys.count(saved_model) > 0 else 0

        selected_model = model_settings_container.selectbox(
            label="Default Model",
            options=available_models.items(),
            format_func=lambda x: x[1],
            index=saved_model_index,
            key=f"system_settings_default_{SystemSettingsKey.MODEL_COLLECTION.name}",
        )
        log.debug(
            "selected model in session state: %s",
            st.session_state[f"system_settings_default_{SystemSettingsKey.MODEL_COLLECTION.name}"][0],
        )
        log.debug("selected model: %s", selected_model[0])
        selected_model_settings: ModelUsageSettingsCollection = get_model_settings_collection(selected_model[0])

        with model_settings_container.expander("Model details"):
            for key, model_settings in selected_model_settings.model_usage_settings.items():
                st.write(f"{model_settings.model_capability.value} model: ")
                st.write(f"- Model Vendor: `{model_settings.model_vendor.value}`")
                st.write(f"- Model Name: `{model_settings.model_name}`")
                st.write(f"- Temperature: `{model_settings.temperature}`")
                st.write(f"- Deployment Name: `{model_settings.model_deployment_name if model_settings.model_deployment_name else 'n/a'}`")
                st.write(f"- License: `{model_settings.license_ if model_settings.license_ else 'unknown'}`")
                st.write(f"- Citation: `{model_settings.citation}`")
                st.divider()


def render_dynamic_options(func: Callable) -> Callable:
    """Renders the dynamic options for a config key."""

    def _drop_down_selector(*args: Any, **kwargs: Any) -> None:
        """Streamlit selectbox for rendering dynamic options."""
        options, fmt, disabled = func(*args, **kwargs)
        configs: dict = kwargs.get("configs", {})
        configkey: ConfigKey = kwargs.get("configkey", None)
        key: str = kwargs.get("key", None)
        selected = configs.get(configkey.key) if configs else None
        st.selectbox(
            f"{configkey.name}{'' if configkey.is_optional else ' *'}",
            options=options,
            key=key,
            format_func=fmt,
            help=configkey.ref_link,
            disabled=disabled,
            index=options.index(selected) if bool(selected and options) else 0,
        )
    return _drop_down_selector


def _get_create_space_config_input_values() -> str:
    """Get values for space creation from session state."""
    space_name = st.session_state.get("create_space_name", "")
    space_summary = st.session_state.get("create_space_summary", "")
    ds_type = st.session_state.get("create_space_ds_type", ["", ""])
    space_configs = f"{space_name}::{space_summary}::{ds_type[1]}"
    return quote_plus(base64.b64encode(space_configs.encode()))


def _get_random_key(prefix: str) -> str:
    return prefix + str(random.randint(0, 1000000)) # noqa E501


def render_gdrive_credential_request(configkey: ConfigKey, key: str, configs: Optional[dict]) -> None:
    """Renders the Google Drive credential request input field with an action burron."""
    creds = configs.get(configkey.key) if configs else st.session_state.get(key, None)
    creds = services.google_drive.validate_credentials(creds)
    info_container = st.empty()
    global opacity
    opacity = 0.4 if creds else 1.0
    st.markdown(f"""
    <style>
      div.element-container .stMarkdown div[data-testid="stMarkdownContainer"] p {{
        margin-bottom: 8px !important;
        font-size: 14px !important;
        opacity: {opacity} !important;
      }}
      div.element-container .stMarkdown div[data-testid="stMarkdownContainer"] style {{
        display: none !important;
      }}
    </style>
    """, unsafe_allow_html=True)
    st.write(f"{configkey.name}{'' if configkey.is_optional else ' *'}")
    text_box, btn = st.columns([3, 1])

    state, resp, auth = None, None, None

    if not creds:
        state = _get_create_space_config_input_values()
        resp, auth = handle_get_gdrive_authurl(state)

    credential_present = bool(creds or resp == services.google_drive.VALID_CREDENTIALS)
    opacity = 0.4 if credential_present else 1.0
    _input_value = '*' * 64 if credential_present else ""

    text_box.text_input(
        configkey.name,
        value=_input_value,
        key=_get_random_key("_input_key"),
        disabled=True, label_visibility="collapsed"
    )

    btn.button(
        "Signin with Google",
        disabled=credential_present,
        key=_get_random_key("_btn_key"),
        on_click=lambda: handle_redirect_to_url(auth, "gdrive") if auth else None,
    )

    if resp == services.google_drive.VALID_CREDENTIALS:
        st.session_state[key] = auth
        st.session_state[configkey.key] = auth

    if resp == services.google_drive.AUTH_WRONG_EMAIL:
        info_container.error("You must authenticate google drive using the same email address for your Docq.AI account")

    if not bool(st.session_state.get(key, None) or creds):
        st.stop()


@render_dynamic_options
def list_gdrive_folders(**kwargs: Any) -> tuple[list, Callable, bool]:
    """List Google Drive folders."""
    configs: dict = kwargs.get("configs", {})
    configkey: ConfigKey = kwargs.get("configkey", None)
    saved_settings = configs.get(configkey.key) if configs else None

    if saved_settings:
        return [saved_settings], lambda x: x["name"], True

    # Make API call to Google Drive to get folders if creating space, i.e No saved settings.
    credential_key = f"{FileStorageServiceKeys.GOOGLE_DRIVE.name}-credential"
    __creds = configs.get(credential_key) if configs else st.session_state.get(credential_key, None)
    creds = services.google_drive.validate_credentials(__creds)

    return (services.google_drive.list_folders(creds), lambda x: x["name"], False) if creds else ([], lambda x: x, False)


def _render_space_data_source_config_input_fields(data_source: Tuple, prefix: str, configs: Optional[dict] = None) -> None:
    fs_handlers = FileStorageServiceHandlers(
        {
            FileStorageServiceKeys.GOOGLE_DRIVE.name: SetFSHandler(
                credential=render_gdrive_credential_request,
                root_path=list_gdrive_folders,
            )
        }
    )

    config_key_list: List[ConfigKey] = data_source[2]

    for configkey in config_key_list:
        _input_key = prefix + "ds_config_" + configkey.key
        service, operation = configkey.key.split("-")
        handler = fs_handlers[service]
        if handler is not None:
            handler(operation, configkey=configkey, key=_input_key, configs=configs)

        else:
            input_type = "password" if configkey.is_secret else "default"
            st.text_input(
                f"{configkey.name}{'' if configkey.is_optional else ' *'}",
                value=configs.get(configkey.key) if configs else "",
                key=_input_key,
                type=input_type,
                help=configkey.ref_link,
                autocomplete="off",  # disable autofill by password manager etc.
            )


def _get_space_defaults() -> Tuple[str, str, str]:
    """Get default values for space creation from query string."""
    space_config = st.experimental_get_query_params().get("state", [None])[0]
    if space_config:
        try:
            space_config = unquote_plus(space_config)
            space_name, space_summary, ds_type = base64.b64decode(space_config).decode("utf-8").split("::")
            st.session_state["create_space_defaults"] = (space_name, space_summary, ds_type)
        except Exception as e:
            st.session_state["create_space_defaults"] = ("", "", "")
            log.error("Error parsing space config from query string: %s", e)
    return st.session_state.get("create_space_defaults", ("", "", ""))


def create_space_ui(expanded: bool = False) -> None:
    """Create a new space."""
    data_sources = list_space_data_source_choices()
    space_name, space_summary, ds_type = _get_space_defaults()
    _prefill_form = bool(space_name or space_summary or ds_type)
    with st.expander("### + New Space", expanded=expanded or _prefill_form):
        st.text_input("Name", value=space_name if space_name else "", key="create_space_name")
        st.text_input("Summary", value=space_summary if space_summary else "", key="create_space_summary")
        ds = st.selectbox(
            "Data Source",
            options=data_sources,
            key="create_space_ds_type",
            format_func=lambda x: x[1],
            index=[x[1] for x in data_sources].index(ds_type) if ds_type else 0,
        )
        if ds:
            _render_space_data_source_config_input_fields(ds, "create_space_")
        if st.button("Create Space"):
            handle_create_space()


def _render_view_space_details_with_container(
    space_data: Tuple, data_source: Tuple, use_expander: bool = False
) -> DeltaGenerator:
    id_, org_id, name, summary, archived, ds_type, ds_configs, created_at, updated_at = space_data
    has_view_perm = org_id == get_selected_org_id()

    if has_view_perm:
        container = st.expander(format_archived(name, archived)) if use_expander else st.container()
        with container:
            if not use_expander:
                st.write(format_archived(name, archived))
            st.write(f"ID: **{id_}**")
            st.write(f"Org ID: **{org_id}**")
            st.write(f"Summary: _{summary}_")
            st.write(f"Type: **{data_source[1]}**")
            st.write(f"Created At: {format_datetime(created_at)} | Updated At: {format_datetime(updated_at)}")
        return container


def _render_edit_space_details_form(space_data: Tuple, data_source: Tuple) -> None:
    id_, org_id, name, summary, archived, ds_type, ds_configs, _, _ = space_data
    has_edit_perm = org_id == get_selected_org_id()

    if has_edit_perm:
        with st.expander("Edit space", expanded=True):
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
            if st.button("Save", key=_get_random_key("_save_btn_key")):
                handle_update_space_details(id_)


def _render_edit_space_details(space_data: Tuple, data_source: Tuple) -> None:
    id_, *_ = space_data

    if st.button("Edit", key=f"update_space_{id_}_button"):
        _render_edit_space_details_form(space_data, data_source)


def _render_manage_space_permissions_form(space_data: Tuple) -> None:
    id_, org_id, *_ = space_data
    has_edit_perm = org_id == get_selected_org_id()

    if has_edit_perm:
        permissions = get_shared_space_permissions(id_)

        with st.expander("Manage Space Permissions", expanded=True):
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
            if st.button("Save"):
                handle_manage_space_permissions(id_)


def _render_manage_space_permissions(space_data: Tuple) -> None:
    id_, *_ = space_data

    if st.button("Permissions", key=f"manage_space_permissions_{id_}_button"):
        _render_manage_space_permissions_form(space_data)


def list_spaces_ui(admin_access: bool = False) -> None:
    """List all spaces."""
    spaces = list_shared_spaces()
    if spaces:
        for s in spaces:
            if s[3] and not admin_access:
                continue
            ds = get_space_data_source_choice_by_type(s[5])
            container = _render_view_space_details_with_container(s, ds, True)
            if admin_access:
                with container:
                    st.markdown(f"[Manage Documents](./Admin_Docs?sid={s[0]})")
                    col_details, col_permissions = st.columns(2)
                    with col_details:
                        _render_edit_space_details(s, ds)
                    with col_permissions:
                        _render_manage_space_permissions(s)
    else:
        st.info("No spaces have been created yet. Please speak to your admin.")


def show_space_details_ui(space: SpaceKey) -> None:
    """Show details of a space."""
    s = get_shared_space(space.id_)
    ds = get_space_data_source_choice_by_type(s[5])
    _render_view_space_details_with_container(s, ds)


def list_logs_ui(type_: LogType) -> None:
    """List logs per log type."""
    st.info("Logs are coming soon.")


def _editor_view(q_param: str) -> None:
    if q_param in st.experimental_get_query_params():
        org_id = get_selected_org_id()
        space = SpaceKey(SpaceType.SHARED, int(st.experimental_get_query_params()[q_param][0]), org_id)
        s = get_shared_space(space.id_)
        if s:
            ds = get_space_data_source_choice_by_type(s[5])
            tab_spaces, tab_docs, tab_edit, tab_permissions = st.tabs(
                ["Space Details", "Manage Documents", "Edit Space", "Permissions"]
            )

            with tab_docs:
                documents_ui(space)
            with tab_spaces:
                show_space_details_ui(space)
            with tab_edit:
                _render_edit_space_details_form(s, ds)
            with tab_permissions:
                _render_manage_space_permissions_form(s)


def admin_docs_ui(q_param: Optional[str] = None) -> None:
    """Manage Documents UI."""
    spaces = list_shared_spaces()
    if spaces:
        st.subheader("Select a space from below:")

        try:  # Get the space id from the query param with prefence to the newly created space.
            _sid = (
                int(st.experimental_get_query_params()[q_param][0])
                if q_param in st.experimental_get_query_params()
                else None
            )
        except ValueError:
            _sid = None
        default_sid = next((i for i, s in enumerate(spaces) if s[0] == _sid), None)

        selected = st.selectbox(
            "Spaces",
            spaces,
            format_func=lambda x: x[2],
            label_visibility="collapsed",
            index=default_sid if default_sid else 0,
        )

        if selected and q_param:
            st.experimental_set_query_params(**{q_param: selected[0]})
        if q_param:
            _editor_view(q_param)


def org_selection_ui() -> None:
    """Render organisation selection UI."""
    try:
        current_org_id = get_selected_org_id()
    except KeyError:
        current_org_id = None
    if current_org_id:
        orgs = handle_list_orgs()

        index__ = next((i for i, s in enumerate(orgs) if s[0] == current_org_id), -1)

        log.debug("org_selection_ui index: %s ", index__)
        log.debug("org_selection_ui() orgs: %s", orgs)
        selected = st.selectbox(
            "Organisation",
            orgs,
            format_func=lambda x: x[1],
            label_visibility="collapsed",
            index=index__,
        )
        if selected:
            handle_org_selection_change(selected[0])


def init_with_pretty_error_ui() -> None:
    """UI to run setup and prevent showing errors to the user."""
    try:
        setup.init()
    except Exception as e:
        st.error("Something went wrong starting Docq.")
        log.fatal("Error: setup.init() failed with %s", e)
        st.stop()


def _validate_name(name: str, generator: DeltaGenerator) -> bool:
    """Validate the name."""
    if not name:
        generator.error("Name is required!")
        return False
    elif len(name) < 3:
        generator.error("Name must be at least 3 characters long!")
        return False
    return True


def _validate_email(email: str, generator: DeltaGenerator, form: str) -> bool:
    """Validate the email."""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not email:
        generator.error("Email is required!")
        return False
    elif len(email) < 3:
        generator.error("Email must be at least 3 characters long!")
        return False
    elif not re.match(email_regex, email):
        generator.error(f"_{email}_ is not a valid email address!")
        return False
    elif handle_check_user_exists(email) and not handle_check_account_activated(email):
        st.session_state[f"{form}-resend-verification-email"] = True
        st.experimental_rerun()
    elif handle_check_user_exists(email) and handle_check_account_activated(email):
        generator.error(f"A user with _{email}_ is already registered!")
        return False
    return True


def _validate_password(password: str, generator: DeltaGenerator) -> bool:
    """Validate the password."""
    special_chars = r"[_@$!#%^&*()-=+\{\}\[\]|\\:;\"'<>,.?/~`]"
    if password is None:
        generator.error("Password is required!")
        return False
    elif len(password) < 8:
        generator.error("Password must be at least 8 characters long and contain atleast 1 of the following: 1 uppercase, 1 lowercase, 1 number and 1 special character.")
        return False
    else:
        password_fmt = {
            "1 lower case letter": re.search(r"[a-z]", password),
            "1 upper case letter": re.search(r"[A-Z]", password),
            "1 number": re.search(r"[0-9]", password),
            "1 special character": re.search(special_chars, password),
        }
        missing_fmt = [k for k, v in password_fmt.items() if not v]
        if missing_fmt:
            error_text = f"Password must contain at least {', '.join(missing_fmt)}."
            if len(missing_fmt) > 1:
                error_text = f"Password must contain at least {', '.join(missing_fmt[:-1])} and {missing_fmt[-1]}."
            generator.error(error_text)
            return False
        return True


def validate_signup_form(form: str = "user-signup") ->bool:
    """Handle validation of the signup form."""
    name: str = st.session_state.get(f"{form}-name", None)
    email: str = st.session_state.get(f"{form}-email", None)
    password: str = st.session_state.get(f"{form}-password", None)
    validator = st.session_state[f"{form}-validator"]

    if not _validate_name(name, validator):
        st.stop()
    if not _validate_email(email, validator, form):
        st.stop()
    if not _validate_password(password, validator):
        st.stop()
    return True


def _disable_sidebar() -> None:
    """Disable the sidebar."""
    st.markdown(
        """<style>
            section[data-testid="stSidebar"] {
              display: none !important;
            }
           </style>
        """,
        unsafe_allow_html=True,
    )


def signup_ui() -> None:
    """Render signup UI."""
    _disable_sidebar()
    handle_logout()
    st.title("Docq Signup")
    st.markdown('Already have an account? Login <a href="/" target="_self">here</a>.', unsafe_allow_html=True)

    if not handle_check_mailer_ready():
        log.error("Mailer service not available due to a config problem. User self signup disabled. All the following env vars needs to be set: DOCQ_SMTP_SERVER, DOCQ_SMTP_PORT, DOCQ_SMTP_LOGIN, DOCQ_SMTP_KEY, DOCQ_SMTP_FROM, DOCQ_SERVER_ADDRESS. Refer to he `misc/secrets.toml.template` in the repo for details.")
        st.error("Unable to create personal accounts.")
        st.info("Please contact your administrator to help you create an account.")
        st.stop()

    form = "user-signup"
    st.session_state[f"{form}-validator"] = st.empty()

    with st.form(key=form):
        st.text_input("Name", placeholder="John Doe", key=f"{form}-name")
        st.text_input("Email", placeholder="johndoe@mail.com", key=f"{form}-email")
        st.text_input(
            "Password",
            type="password",
            key=f"{form}-password",
            help="Password must be at least 8 characters long and contain at least 1 lowercase letter, 1 uppercase letter, 1 number and 1 special character."
        )
        submit = st.form_submit_button("Signup")
        if submit:
            validate_signup_form()
            handle_user_signup()

    if st.session_state.get(f"{form}-resend-verification-email", False):
            with st.session_state[f"{form}-validator"].container():
                __resend_verification_ui(st.session_state[f"{form}-email"], form)


def verify_email_ui() -> None:
    """UI for verifying email."""
    _disable_sidebar()
    handle_logout()
    if handle_verify_email():
        st.success("Email address verified and account activated. Thank you for signing up for Docq.")
        st.markdown('You can now Access docq from <a href="/" target="_self">here</a>.', unsafe_allow_html=True)
    else:
        st.error("Email verification failed!")
        st.info("Please try again or contact your administrator.")
