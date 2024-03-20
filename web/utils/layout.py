"""Layout components for the web app."""
import base64
import contextlib
import json
import logging as log
import os
import random
import re
from typing import Callable, List, Literal, Optional, Tuple
from urllib.parse import quote_plus, unquote_plus

import docq
import streamlit as st
from docq import setup
from docq.access_control.main import SpaceAccessType
from docq.config import (
    LogType,
    OrganisationFeatureType,
    OrganisationSettingsKey,
    SpaceType,
    SystemFeatureType,
    SystemSettingsKey,
)
from docq.domain import AssistantType, ConfigKey, DocumentListItem, FeatureKey, SpaceKey
from docq.extensions import ExtensionContext
from docq.integrations.models import SlackInstallation
from docq.manage_assistants import list_assistants
from docq.model_selection.main import (
    LlmUsageSettingsCollection,
    get_model_settings_collection,
    list_available_model_settings_collections,
)
from docq.support.auth_utils import (
    get_cache_auth_session,
    reset_cache_and_cookie_auth_session,
    verify_cookie_hmac_session_id,
)
from opentelemetry import trace
from st_pages import hide_pages, translate_icon
from streamlit.components.v1 import html
from streamlit.delta_generator import DeltaGenerator
from streamlit.elements.image import AtomicImage
from streamlit.errors import StreamlitAPIException
from streamlit.runtime.scriptrunner import get_script_run_ctx
from streamlit.source_util import get_pages

from .constants import ALLOWED_DOC_EXTS, SessionKeyNameForAuth, SessionKeyNameForChat
from .error_ui import _handle_error_state_ui
from .formatters import format_archived, format_datetime, format_duration, format_filesize, format_timestamp
from .handlers import (
    _set_session_state_configs,
    get_enabled_org_features,
    get_enabled_system_features,
    get_max_number_of_documents,
    get_organisation_settings,
    get_shared_space,
    get_shared_space_permissions,
    get_space_data_source,
    get_space_data_source_choice_by_type,
    handle_archive_org,
    handle_chat_input,
    handle_check_account_activated,
    handle_check_mailer_ready,
    handle_check_user_exists,
    handle_click_chat_history_thread,
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
    handle_fire_extensions_callbacks,
    handle_get_chat_history_threads,
    handle_get_gravatar_url,
    handle_get_system_settings,
    handle_get_thread_space,
    handle_get_user_email,
    handle_index_thread_space,
    handle_install_docq_slack_application,
    handle_list_documents,
    handle_list_orgs,
    handle_list_slack_channels,
    handle_list_slack_installations,
    handle_login,
    handle_logout,
    handle_manage_space_permissions,
    handle_org_selection_change,
    handle_public_session,
    handle_redirect_to_url,
    handle_reindex_space,
    handle_resend_email_verification,
    handle_update_org,
    handle_update_organisation_settings,
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
from .layout_assistants import render_assistants_selector_ui
from .sessions import (
    get_auth_session,
    get_authenticated_user_id,
    get_chat_session,
    get_public_session_id,
    get_public_space_group_id,
    get_selected_assistant,
    get_selected_org_id,
    is_current_user_super_admin,
    reset_session_state,
    session_state_exists,
    set_selected_assistant,
)
from .streamlit_application import st_app

tracer = trace.get_tracer(__name__, docq.__version_str__)


__chat_ui_script = """
<script>
    parent = window.parent.document || window.document

    function setStyle() {
        const id = 'docq-chat-ui-style-declaration'
        const previousStyle = parent.getElementById(id)
        if (previousStyle) previousStyle.remove();
        const style = document.createElement('style')
        style.setAttribute('type', 'text/css')
        style.setAttribute('id', id)

        style.innerHTML = `
            section[tabindex="0"] [data-testid="stExpander"] {
                --background-color: ${getComputedStyle(parent.body, null).getPropertyValue('background-color')};
            }
        `
        parent.head.appendChild(style);
        setExpanderLabels();
        setButtonLabels();
    }; setStyle();

    const observer = new MutationObserver(setStyle)
    observer.observe(parent.body, { attributes: true, attributeFilter: ['style'] })


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


    /**
     * 1. Find all expanders
     * 2. For each expander set an attribute 'docq-data-label' with the expander's label text
     * Note: label is nested under summary > span > div > p
     */
    function setExpanderLabels() {
        const expanders = parent.querySelectorAll('[data-testid="stExpander"]');
        expanders.forEach((el) => {
            const label = el.querySelector('summary > span > div > p').innerText
            el.setAttribute('docq-data-label', label)
        })
    };

    /**
     * 1. Find all buttons with attribute kind="primary"
     * 2. For each button set an attribute 'docq-data-label' with the button's label text
     */
    function setButtonLabels() {
        const buttons = parent.querySelectorAll('.row-widget.stButton');
        buttons.forEach((el) => {
            el.parentElement.setAttribute('docq-data-label', el.innerText)
            el.parentElement.removeAttribute('width')
            el.removeAttribute('style')
        })
    };

</script>
"""


def _chat_ui_script() -> None:
    """A javascript snippet that runs on the chat UI."""
    html(__chat_ui_script, height=0)


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


@tracer.start_as_current_span("__no_admin_menu")
def __no_admin_menu() -> None:
    hide_pages(["Admin_Section"])
    hide_pages(["ML Engineering"])


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


def __hide_all_empty_divs() -> None:
    """Hide all empty divs containing style or iframe that doesent render anything."""
    st.markdown(
        """<style>
        div:has(> div.stMarkdown > div[data-testid="stMarkdownContainer"] > style) {
            display: none !important;
        }
        div:has(> iframe[height="0"]) {
            display: none !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def __always_hidden_pages() -> None:
    """These pages are always hidden whether the user is an admin or not."""
    hide_pages(["widget", "signup", "verify", "Admin_Spaces"])


def render_page_title_and_favicon(page_display_title: Optional[str] = None, browser_title: Optional[str] = None) -> None:
    """Handle setting browser page title and favicon. Separately render in app page title with icon defined in show_pages().

    Args:
        page_display_title: Optional[str] - override the title rendered on the page and browser tab.
    """
    favicon_path = "web/favicon.ico"
    browser_title_prefix = "Docq.AI"
    about_menu_content = f"**{docq.__summary__}** \
            \n\nVersion: **{docq.__version__}** \
            \nWebsite: {docq.__homepage_url__}  \
            \nDocs: {docq.__documentation_url__} \
            \nGitHub (give us a star): {docq.__repository_url__} \
            \nTwitter: https://twitter.com/docqai"

    pages = get_pages("")
    ctx = get_script_run_ctx()

    if ctx is None:
        return

    try:
        current_page = pages[ctx.page_script_hash]
    except KeyError:
        try:
            current_page = [p for p in pages.values() if p["relative_page_hash"] == ctx.page_script_hash][0]
        except IndexError:
            return

    page_slug = current_page["page_name"]  # this is the URL slug defined in show_pages()
    page_icon = current_page["icon"]  # the optional icon defined in show_pages()
    _page_display_title = page_display_title or page_slug.replace("_", " ")

    try:
        ctx._set_page_config_allowed = True
        st.set_page_config(
            page_icon=favicon_path,
            page_title= browser_title if browser_title else f"{browser_title_prefix} - {_page_display_title}",
            menu_items={"About": about_menu_content},
        )
    except StreamlitAPIException:
        pass

    if page_icon and not page_display_title:
        st.title(f"{translate_icon(page_icon)} {_page_display_title}")
    else:
        st.title(_page_display_title)


def render_docq_logo() -> None:
    """Render the Docq logo."""
    st.markdown(
        "<img src='https://raw.githubusercontent.com/docqai/docq/main/docs/assets/logo.jpg'  width='100' alt='Docq.AI Logo'/>",
        unsafe_allow_html=True,
    )


def __resend_verification_ui(
    username: str,
    form: str,
) -> None:
    """Resend email verification UI."""
    msg = st.empty()
    msg.error("Your account is not activated. Please check your email for the activation link.")
    _, center, _ = st.columns([1, 1, 1])
    if handle_check_mailer_ready() and center.button("Resend verification email"):
        handle_resend_email_verification(username)
        st.session_state[f"{form}-resend-verification-email"] = False
        msg.success("Verification email sent. Please check your email.")
    st.stop()


@tracer.start_as_current_span("render __login_form")
def __login_form() -> None:
    __no_admin_menu()

    if system_feature_enabled(SystemFeatureType.FREE_USER_SIGNUP, show_message=False):
        st.markdown("Don't have an account? Signup <a href='/signup' target='_self'>here</a>", unsafe_allow_html=True)
    else:
        st.markdown(
            "Don't have an account? Subscribe on our website <a href='https://docq.ai/#plans' target='_blank'>here</a>",
            unsafe_allow_html=True,
        )

    st.markdown("### Please login to continue")
    form_validator, form_name = st.empty(), "login-form"
    with st.form(key=form_name):
        username = st.text_input("Username", value="", key="login_username", autocomplete="username")
        password = st.text_input(
            "Password", value="", key="login_password", type="password", autocomplete="current-password"
        )
        if st.form_submit_button("Login"):
            if handle_login(username, password):
                st.rerun()
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
        st.rerun()


def __not_authorised() -> None:
    st.error("You are not authorized to access this page / section.")
    st.info(
        f"You're logged in as `{get_auth_session()[SessionKeyNameForAuth.NAME.name]}`. Please login as a different user with correct permissions to try again."
    )
    st.stop()


def public_access() -> None:
    """Menu options for public access."""
    # __no_staff_menu()
    __no_admin_menu()
    __always_hidden_pages()
    __hide_all_empty_divs()


@tracer.start_as_current_span("auth_required")
def auth_required(
    show_login_form: bool = True, requiring_selected_org_admin: bool = False, show_logout_button: bool = True
) -> bool:
    """Decide layout based on current user's access."""
    log.debug("auth_required() called")
    span = trace.get_current_span()
    span.add_event("Checking authorisation")
    auth = None
    __always_hidden_pages()
    __hide_all_empty_divs()

    session_state_existed = session_state_exists()
    log.debug("auth_required(): session_state_existed: %s", session_state_existed)
    span.add_event("session state existed", {"result": session_state_existed})
    if session_state_existed:
        auth = get_auth_session()
    elif verify_cookie_hmac_session_id() is not None:
        # there's a valid auth session token. Let's get session state from cache.
        auth = get_cache_auth_session()
        log.debug("auth_required(): Got auth session state from cache: %s", auth)
        span.add_event("Got auth session state from cache")

    if auth:
        log.debug("auth_required(): Valid auth session found: %s", auth)
        span.add_event("Valid auth session found")
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
            if requiring_selected_org_admin:
                __not_authorised()
                return False
        return True
    else:
        log.debug("auth_required(): No valid auth session found. User needs to re-authenticate.")
        span.add_event("No valid auth session found")
        reset_session_state()
        reset_cache_and_cookie_auth_session()
        if show_login_form:
            __login_form()
        return False


def is_super_admin() -> bool:
    """Check if the current user is a super admin. auth_required() must be called before this."""
    auth = get_auth_session()
    is_super_admin = auth.get(SessionKeyNameForAuth.SUPER_ADMIN.name, False)
    if not is_super_admin:
        __not_authorised()
    return is_super_admin


def public_session_setup() -> None:
    """Initialize session state for the public pages."""
    handle_public_session()


def org_feature_enabled(feature: OrganisationFeatureType) -> bool:
    """Check if a org level feature is enabled."""
    feats = get_enabled_org_features()
    if feats and feature.name not in feats:
        st.error("This organisation level feature is not enabled.")
        st.info("Please contact your administrator to enable this feature.")
        st.stop()
        return False
    return True


@tracer.start_as_current_span("system_feature_enabled")
def system_feature_enabled(feature: SystemFeatureType, show_message: bool = True) -> bool:
    """Check if a system level feature is enabled."""
    span = trace.get_current_span()
    feats = get_enabled_system_features()
    span.add_event("loaded enabled features", attributes={"enabled_features": str(feats)})
    feat_enabled = False
    if feats and feature.name in feats:
        feat_enabled = True

    if not feat_enabled and show_message:
        st.error("This system level feature is not enabled.")
        st.info("Please contact your administrator to enable this feature.")
        st.stop()

    span.set_attributes({"system_feature.name": feature.name, "system_feature.enabled": feat_enabled})
    return feat_enabled


def public_space_enabled(feature: OrganisationFeatureType) -> None:
    """Check if public space is ready."""
    __embed_page_config()
    org_feature_enabled(feature)
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
        [docq-data-label="Including these shared spaces:"] {
            z-index: 1000;
            position: fixed;
            top: 46px;
            width: inherit;
            background-color: var(--background-color);
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def _show_chat_histories(feature: FeatureKey) -> None:
    st.markdown(
        """
      <style>
        section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] div[data-testid="stExpander"] button[kind="secondary"] {
            width: 100%;
            text-align: left !important;
            justify-content: flex-start;
            padding: 0px 1rem;
            min-height: unset !important;
            max-height: 2rem !important;
            height: 2rem;
            border-radius: 5px;
            overflow: hidden;
        }
         section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] div[data-testid="stExpander"] h4 {
            margin-bottom: 0.5rem;
        }
         section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] div[data-testid="stExpander"] button[kind="secondary"] p {
            padding-top: 0.3rem;
            max-height: 1.6rem;
            overflow: hidden;
            display: inline-block !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
            gap: 2px !important;
        }
      </style>
    """,
        unsafe_allow_html=True,
    )
    with st.sidebar.expander("Chat History"):
        chat_threads = handle_get_chat_history_threads(feature)
        day = None
        for x in chat_threads:
            if day is None:
                day = format_duration(x[2])
                st.markdown(f"#### {day}")
            if format_duration(x[2]) != day:
                day = format_duration(x[2])
                st.markdown(f"#### {day}")
            st.button(
                x[1],
                key=f"{x[1]}-{x[0]}",
                on_click=handle_click_chat_history_thread,
                args=(
                    feature,
                    x[0],
                ),
            )


def _render_documents_list_ui(space: SpaceKey, read_only: bool = True, size: Literal["lg", "sm"] = "lg", expander_label: str = "Documents List") -> None:
    """Render the UI for listing documents in a space."""
    expander_selector = f'div[data-testid="stExpander"][docq-data-label="{expander_label}"]'

    st.markdown(f"""
        <style>
          {expander_selector} hr {{
            margin-top: 0.5rem;
          }}
          {expander_selector} button[kind="primary"] {{
            min-height: unset;
            height: 1.5rem;
          }}
          {expander_selector} button[kind="secondary"] {{
            justify-content: center !important;
          }}
        </style>
        """,
        unsafe_allow_html=True
    )
    documents: List[DocumentListItem] = handle_list_documents(space)
    if documents:
        st.markdown(f"**Document Count**: {len(documents)}")
        st.divider()
        for i, document in enumerate(documents):
            with st.container():
                st.markdown(f"**{document.link}**")
                st.markdown(
                    f"Size: {format_filesize(document.size)} | Last Modified: {format_timestamp(document.indexed_on)}"
                )
                if not read_only:
                    st.button(
                        "Delete file",
                        type="secondary" if size == "lg" else "primary",
                        key=f"delete_file_{i}_{space.value()}",
                        on_click=handle_delete_document,
                        args=(
                            document.link,
                            space,
                        ),
                    )
                    st.divider()

        if not read_only:
            st.button(
                "Delete all documents",
                key=f"delete_all_files_{space.value()}",
                on_click=handle_delete_all_documents,
                args=(space,),
            )
    else:
        st.info("No documents.")


def _render_show_thread_space_files(feature: FeatureKey) -> None:
    """Show file uploads within a chat thread space."""
    if feature.type_ == OrganisationFeatureType.ASK_SHARED:
        with st.sidebar.container():
            space = handle_get_thread_space(feature)
            if space:
                expander_label = "Knowledge"
                with st.expander(expander_label):
                    _render_documents_list_ui(space, False, "sm", expander_label)


def _render_assistant_selection(feature: FeatureKey) -> None:
    with st.sidebar.container():
        selected_org_id = get_selected_org_id()

        if feature.type_ == OrganisationFeatureType.CHAT_PRIVATE:
            assistant_type = AssistantType.SIMPLE_CHAT
        elif feature.type_ == OrganisationFeatureType.ASK_SHARED:
            assistant_type = AssistantType.ASK

        assistants_data_org = list_assistants(org_id=selected_org_id, assistant_type=assistant_type)
        assistants_data_global = list_assistants(assistant_type=assistant_type)
        assistants_data = assistants_data_org + assistants_data_global

        selected_assistant_scoped_id = get_selected_assistant()

        selected = render_assistants_selector_ui(
            assistants_data=assistants_data, selected_assistant_scoped_id=selected_assistant_scoped_id
        )

        if selected:
            selected_assistant_scoped_id = selected[9]
            set_selected_assistant(selected_assistant_scoped_id)


def _render_chat_file_uploader(feature: FeatureKey, key_suffix: int) -> None:
    """Upload files to chat."""
    if feature.type_ != OrganisationFeatureType.ASK_SHARED:
        return None

    st.markdown(
        """
    <style>
      div[data-testid="stFileUploader"] label {
        display: none;
      }
      section[data-testid="stFileUploadDropzone"] {
        height: 2.1rem;
        margin-left: 0.2rem;
      }
      section[data-testid="stFileUploadDropzone"] div {
        flex-direction: row;
        gap: 1rem;
      }
      section[data-testid="stFileUploadDropzone"] :is(small, span) {
        justify-content: center;
        align-items: center;
        display: flex;
        margin: 0;
      }
      section[data-testid="stFileUploadDropzone"] small {
        font-size: 0;
      }
      section[data-testid="stFileUploadDropzone"] small:after {
        content: "File limit 200MB";
        font-size: 0.8rem;
      }
      section[data-testid="stFileUploadDropzone"] button[data-testid="baseButton-secondary"] {
        min-height: unset;
        height: 1.8rem;
        font-size: 0.8rem;
      }
      div[data-testid="stFileUploader"]:has(.uploadedFile) section[data-testid="stFileUploadDropzone"] {
        display: none;
      }
      div[data-testid="stHorizontalBlock"]:has([data-testid="stSpinner"]) div:has(> ul > li > .uploadedFile) {
        display: none !important;
      }
      div:has(> ul > li > .uploadedFile) {
        margin: 0 !important;
        padding: 0 !important;
      }
    </style>
    """,
        unsafe_allow_html=True,
    )
    input_key = f"chat_file_uploader_{feature.value()}_{key_suffix}"
    if st.file_uploader(":paperclip:", key=input_key, type=ALLOWED_DOC_EXTS):
        st.session_state[f"chat_file_uploader_{feature.value()}"] = st.session_state[input_key]
        filename = st.session_state[input_key].name
        with st.spinner(f"Indexing file: {filename[:100]} ..."):
            handle_index_thread_space(feature)
            st.session_state[f"chat_file_uploader_{feature.value()}"] = None


def chat_ui(feature: FeatureKey) -> None:
    """Chat UI layout."""
    prepare_for_chat(feature)
    st.markdown(
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

            div[data-testid="stHorizontalBlock"]:has(div > div > div > [docq-data-label="New chat"]) {
                position: fixed;
                bottom: 1.8rem;
                z-index: 1000;
                max-height: 2rem;
            }

            div[data-testid="column"] > div > div > [docq-data-label="New chat"] > .stButton {
                display: flex;
                align-items: center;
                justify-content: flex-end;
            }

            [docq-data-label="New chat"] button {
                min-height: unset;
                height: 2rem;
                font-size: 0.8rem;
            }

            [docq-data-label="Load chat history earlier"] .stButton {
                display: flex;
                justify-content: center;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )
    from docq.agents.datamodels import Message

    with st.container():
        if feature.type_ == OrganisationFeatureType.ASK_SHARED:
            _personal_ask_style()
            with st.container().expander("Including these shared spaces:", True):
                spaces = list_shared_spaces()
                st.multiselect(
                    "Including these shared spaces:",
                    options=spaces,
                    default=spaces,
                    format_func=lambda x: x[2],
                    key=f"chat_shared_spaces_{feature.value()}",
                    label_visibility="collapsed",
                )

        if st.button("Load chat history earlier"):
            query_chat_history(feature)

    with st.container():
        # day = format_datetime(get_chat_session(feature.type_, SessionKeyNameForChat.CUTOFF))
        # st.markdown(f"#### {day}")

        chat_history = get_chat_session(feature.type_, SessionKeyNameForChat.HISTORY)

        if chat_history:
            for x in chat_history:
                # x = (id, text, is_user, time, thread_id)
                # if format_datetime(x[3]) != day:
                #     day = format_datetime(x[3])
                #     st.markdown(f"#### {day}")

                agent_output = None
                with contextlib.suppress(Exception):
                    #TODO: this is a hack. A data structure with a pydantic model should be implemented to replace the list of tuples.
                    # agent messages are serialised Message dataclass. Other messages are str.
                    _x = json.loads(x[1])
                    agent_output = Message(
                        **_x
                    )  # if the message payload isn't a serialised Message class an exception will be raised and we ignore it.

                if agent_output and agent_output.metadata:
                    with st.chat_message(
                        "assistant", avatar="https://github.com/docqai/docq/blob/main/docs/assets/logo.jpg?raw=true"
                    ):
                        st.write(agent_output.content)
                        with st.expander("Agent Messages", False):
                            for m in agent_output.metadata["messages"]:
                                if m["content"] != "":
                                    st.write(m["role"], "\n\n", m["content"])
                                    st.divider()
                        with st.expander("Files", True):
                            files = agent_output.metadata["files"]
                            if files:
                                images: list[AtomicImage] = []
                                image_names = []
                                for file in files:
                                    if file["type"] == "image":
                                        images.append(os.path.join("./.persisted/agents", file["path"]))
                                        image_names.append(file["name"])
                                    elif file["type"] == "code":  # noqa: SIM114
                                        images.append(os.path.join("./web/icons/flaticon/001-py.png"))
                                        image_names.append(file["name"])
                                    elif file["type"] == "pdf":
                                        images.append(os.path.join("./web/icons/flaticon/003-pdf-file.png"))
                                        image_names.append(file["name"])
                                    else:
                                        st.write(file["name"])

                                st.image(images, image_names)

                else:
                    _chat_message(x[1], x[2])

    st.chat_input(
        "Type your question here",
        key=f"chat_input_{feature.value()}",
        on_submit=handle_chat_input,
        args=(feature,),
    )

    uploader, new_chat = st.columns([3, 1])
    if new_chat.button("New chat"):
        handle_create_new_chat(feature)
        st.rerun()

    thread_id = get_chat_session(feature.type_, SessionKeyNameForChat.THREAD)

    with uploader:
        _render_chat_file_uploader(feature, thread_id)

    _render_show_thread_space_files(feature)
    _render_assistant_selection(feature)
    _show_chat_histories(feature)
    _chat_ui_script()


def _render_document_upload(space: SpaceKey, documents: List) -> None:
    max_size = get_max_number_of_documents()
    if len(documents) < max_size:
        with st.form("Upload", clear_on_submit=True):
            st.file_uploader(
                "Upload your documents here",
                type=ALLOWED_DOC_EXTS,
                key=f"uploaded_file_{space.value()}",
                accept_multiple_files=True,
            )
            st.form_submit_button(label="Save files", on_click=handle_upload_file, args=(space,))
    else:
        st.warning(f"You cannot upload more than {max_size} documents.")


def documents_ui(space: SpaceKey) -> None:
    """Displays the UI for managing documents in a space."""
    permission = get_shared_space_permissions(space.id_)
    if permission.get(SpaceAccessType.PUBLIC, False):
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
        label = "Documents"
        st.markdown("""
            <style>
              div[data-testid="stExpander"] hr {
                margin-top: 0.5rem;
              }
            </style>
            """,
            unsafe_allow_html=True
        )
        with st.expander(label):
            _render_documents_list_ui(space, read_only=not show_delete, expander_label=label)
    else:
        st.info("No documents or the space does not support listing documents.")


def chat_settings_ui(feature: FeatureKey) -> None:
    """Chat settings."""
    st.info("Settings for general chat are coming soon.")


@tracer.start_as_current_span("system_settings_ui")
def system_settings_ui() -> None:
    """System settings."""
    span = trace.get_current_span()
    settings = handle_get_system_settings()
    log.debug("saved system settings raw: %s", settings)

    span.add_event("loaded saved system settings", attributes={"settings.system": settings.__str__()})
    st.write("**System Settings**")
    with st.form(key="system_settings"):
        enabled_system_features_container = st.container()

        st.form_submit_button(
            label="Save",
            on_click=handle_update_system_settings,
        )
        default_selection = (
            [SystemFeatureType.__members__[k] for k in settings[SystemSettingsKey.ENABLED_FEATURES.name]]
            if settings
            else []
        )  # [f for f in SystemFeatureType],
        enabled_system_features_container.multiselect(
            SystemSettingsKey.ENABLED_FEATURES.value,
            options=[f for f in SystemFeatureType],
            format_func=lambda x: x.value,
            default=default_selection,
            key=f"system_settings_{SystemSettingsKey.ENABLED_FEATURES.name}",
        )


@tracer.start_as_current_span("organisation_settings_ui")
def organisation_settings_ui() -> None:
    """Org settings."""
    span = trace.get_current_span()
    settings = get_organisation_settings()
    log.debug("saved org settings raw: %s", settings)
    span.add_event("loaded saved org settings", attributes={"settings.organisation": settings.__str__()})
    st.write("**Organisation Settings**")
    with st.form(key="org_settings"):
        enabled_features_container = st.container()

        model_settings_container = st.container()

        st.form_submit_button(
            label="Save",
            on_click=handle_update_organisation_settings,
        )
        default_selection = (
            [OrganisationFeatureType.__members__[k] for k in settings[OrganisationSettingsKey.ENABLED_FEATURES.name]]
            if settings
            else []
        )
        enabled_features_container.multiselect(
            OrganisationSettingsKey.ENABLED_FEATURES.value,
            options=[f for f in OrganisationFeatureType],
            format_func=lambda x: x.value,
            default=default_selection,
            key=f"org_settings_{OrganisationSettingsKey.ENABLED_FEATURES.name}",
        )

        available_models = list_available_model_settings_collections()
        log.debug("available models %s", available_models)
        saved_model = (
            settings[OrganisationSettingsKey.MODEL_COLLECTION.name]
            if OrganisationSettingsKey.MODEL_COLLECTION.name in settings
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
            key=f"org_settings_default_{OrganisationSettingsKey.MODEL_COLLECTION.name}",
        )
        log.debug(
            "selected model in session state: %s",
            st.session_state[f"org_settings_default_{OrganisationSettingsKey.MODEL_COLLECTION.name}"][0],
        )
        log.debug("selected model: %s", selected_model[0])
        selected_model_settings: LlmUsageSettingsCollection = get_model_settings_collection(selected_model[0])

        with model_settings_container.expander("Model details"):
            for _, model_settings in selected_model_settings.model_usage_settings.items():
                st.write(f"{model_settings.model_capability.value} model: ")
                st.write(f"- Model Vendor: `{model_settings.service_instance_config.vendor.value}`")
                st.write(f"- Model Name: `{model_settings.service_instance_config.model_name}`")
                st.write(f"- Temperature: `{model_settings.temperature}`")
                st.write(
                    f"- Deployment Name: `{model_settings.service_instance_config.model_deployment_name if model_settings.service_instance_config.model_deployment_name else 'n/a'}`"
                )
                st.write(
                    f"- License: `{model_settings.service_instance_config.license_ if model_settings.service_instance_config.license_ else 'unknown'}`"
                )
                st.write(f"- Citation: `{model_settings.service_instance_config.citation}`")
                st.divider()


def _get_create_space_config_input_values() -> str:
    """Get values for space creation from session state."""
    space_name = st.session_state.get("create_space_name", "")
    space_summary = st.session_state.get("create_space_summary", "")
    ds_type = st.session_state.get("create_space_ds_type", ["", ""])
    space_configs = f"{space_name}::{space_summary}::{ds_type[1]}"
    return quote_plus(base64.b64encode(space_configs.encode()))


def _get_random_key(prefix: str) -> str:
    return prefix + str(random.randint(0, 1000000))  # noqa E501


def _get_credential_request_params() -> dict:
    return {
        "code": st.query_params.get("code", None),
        "email": handle_get_user_email(),
        "state": _get_create_space_config_input_values(),
    }


def _render_file_storage_credential_request(configkey: ConfigKey, key: str, configs: Optional[dict]) -> None:
    """Renders the credential request input field with an action button."""
    saved_credentials = configs.get(configkey.key) if configs else st.session_state.get(key, None)
    st.markdown(
        """
    <style>
      div.element-container .stMarkdown div[data-testid="stMarkdownContainer"] p {
        margin-bottom: 8px !important;
        font-size: 14px !important;
      }
      div.element-container .stMarkdown div[data-testid="stMarkdownContainer"] style {
        display: none !important;
      }
    </style>
    """,
        unsafe_allow_html=True,
    )
    st.write(f"{configkey.name}{'' if configkey.is_optional else ' *'}")
    text_box, btn = st.columns([2, 1])

    new_credentials, auth_url = None, None

    if saved_credentials is None:
        params = _get_credential_request_params()
        handler = configkey.options.get("handler", None) if configkey.options else None
        response = handler(params) if handler else {}
        new_credentials = response.get("credential") if response else None
        auth_url = response.get("auth_url") if response else None

    text_box.text_input(
        configkey.name,
        value="*" * 64 if bool(new_credentials or saved_credentials) else "",
        key=_get_random_key("_input_key"),
        disabled=True,
        label_visibility="collapsed",
    )

    btn.button(
        configkey.options.get("btn_label", "Get Credential") if configkey.options else "Get Credentials",
        disabled=bool(saved_credentials or new_credentials),
        key=_get_random_key("_btn_key"),
        on_click=lambda: handle_redirect_to_url(auth_url, "gdrive") if auth_url else None,
    )

    if not bool(saved_credentials or new_credentials):
        st.stop()

    if new_credentials is not None:
        st.session_state[key] = new_credentials or saved_credentials
        st.session_state[configkey.key] = new_credentials or saved_credentials
        st.query_params.clear()


def fetch_file_storage_root_folders(_configkey: ConfigKey, configs: Optional[dict]) -> tuple[list[dict], bool]:
    """List File Storage System root foldesrs."""
    saved_settings = configs.get(_configkey.key) if configs else None
    options = _configkey.options if _configkey.options else {}
    if saved_settings is not None:
        return [saved_settings], True

    else:
        with st.spinner("Loading Options..."):  # noqa E501
            handler: Callable = options.get("handler", None)
            if handler:
                return handler(configs, st.session_state)
            return [], False


def _set_options(configkey: ConfigKey, key: str, configs: Optional[dict]) -> None:
    st.session_state[key] = (
        *fetch_file_storage_root_folders(configkey, configs),
        configs.get(configkey.key) if configs else None,
    )


def _render_file_storage_root_path_options(configkey: ConfigKey, key: str, configs: Optional[dict]) -> None:
    """Renders the dynamic options for a config key."""
    temp_key = f"{key}_temp"

    if temp_key not in st.session_state:
        _set_options(configkey, temp_key, configs)

    options, disabled, selected = st.session_state[temp_key]
    if not options:
        _set_options(configkey, temp_key, configs)
        options, disabled, selected = st.session_state[temp_key]

    fmt_func = configkey.options.get("format_function", None) if configkey.options else None

    st.selectbox(
        f"{configkey.name}{'' if configkey.is_optional else ' *'}",
        options=options,
        key=key,
        format_func=fmt_func if fmt_func else lambda x: x,
        help=configkey.ref_link,
        disabled=disabled,
        index=options.index(selected) if bool(selected and options) else 0,
    )


def _handle_custom_input_field(configkey: ConfigKey, key: str, configs: Optional[dict]) -> None:
    """Handle Ui interactions."""
    if configkey.options and configkey.options.get("type") == "credential":
        _render_file_storage_credential_request(configkey, key, configs)
    elif configkey.options and configkey.options.get("type") == "root_path":
        _render_file_storage_root_path_options(configkey, key, configs)
    if configkey.options and configkey.options.get("type") == "selectbox":
        if configs:
            source_page_type_str = configs.get("source_page_type")

            options_data: dict[str, str] = configkey.options.get("select_box_options", [])
            selected_option_index = 0
            try:
                selected_option_index = (
                    list(options_data.keys()).index(source_page_type_str[0]) if source_page_type_str else 0
                )
            except ValueError:
                log.error("source_page_type_str '%s' not a key in the 'select_box_options' list.", source_page_type_str)

            st.selectbox(
                label=f"{configkey.name}{'' if configkey.is_optional else ' *'}",
                options=options_data.items(),
                format_func=lambda x: x[1],
                index=selected_option_index,
                key=key,
                help="Index Page: A url to a page web page with a list of links to scrape. Page List: a command separated list of URLs to scrape",
            )
        else:
            log.error(
                "input field type 'selectbox' requires options with 'select_box_options' object", str(configkey.options)
            )
    else:
        log.error("Unknown custom input field type: %s", str(configkey.options))


def _render_space_data_source_config_input_fields(
    data_source: Tuple, prefix: str, configs: Optional[dict] = None
) -> None:
    config_key_list: List[ConfigKey] = data_source[2]

    for configkey in config_key_list:
        print("configkey", configkey)
        _input_key = prefix + "ds_config_" + configkey.key
        if configkey.options and configkey.options.get("type", None):
            _handle_custom_input_field(configkey, _input_key, configs)

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

def _get_create_space_form_values() -> Tuple[str, str, str]:
    """Get default values for space creation from query string."""
    space_config = st.query_params.get("state", None)
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
    space_name, space_summary, ds_type = _get_create_space_form_values()
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
            st.session_state["create_space_defaults"] = ("", "", "")
            space = handle_create_space()
            st.query_params['sid'] = str(space.id_)


def _render_view_space_details_with_container(
    space_data: Tuple, data_source: Tuple, use_expander: bool = False
) -> DeltaGenerator:
    id_, org_id, name, summary, archived, ds_type, ds_configs, _, created_at, updated_at = space_data
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
    id_, org_id, name, summary, archived, ds_type, ds_configs, *_ = space_data
    has_edit_perm = org_id == get_selected_org_id()
    print("load space data:", space_data)
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
            print(">>>>>>1")
            _render_space_data_source_config_input_fields(data_source, f"update_space_details_{id_}_", ds_configs)
            print(">>>>>>2")
            # if st.button("Save", key=_get_random_key("_save_btn_key")):
            if st.button("Save", key="space_update_save_btn_key"):
                print(">>>>>>3")
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
            if s[4] and not admin_access:  # Skip if archived and not admin.
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
        st.info("No spaces have been created yet. If you are an admin goto 'Admin Section > Admin Spaces' to create a Shared Space.")


def show_space_details_ui(space: SpaceKey) -> None:
    """Show details of a space."""
    s = get_shared_space(space.id_)
    ds = get_space_data_source_choice_by_type(s[5])
    _render_view_space_details_with_container(s, ds)


def list_logs_ui(type_: LogType) -> None:
    """List logs per log type."""
    st.info("Logs are coming soon.")


def _editor_view(q_param: str) -> None:
    if q_param in st.query_params.to_dict():
        org_id = get_selected_org_id()
        space = SpaceKey(SpaceType.SHARED, int(st.query_params[q_param]), org_id)
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
                int(st.query_params[q_param])
                if q_param in st.query_params.to_dict()
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
            st.query_params[q_param] = str(selected[0])
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
        log.debug("Tornado settings: %s ", st_app.get_singleton_instance().settings)
    except Exception as e:
        st.error("Something went wrong starting Docq.")
        log.fatal("Error: setup.init() failed with: %s", e, exc_info=True)
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
        st.rerun()
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
        generator.error(
            "Password must be at least 8 characters long and contain atleast 1 of the following: 1 uppercase, 1 lowercase, 1 number and 1 special character."
        )
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


def validate_signup_form(form: str = "user-signup") -> bool:
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


@tracer.start_as_current_span("signup_ui")
def signup_ui() -> None:
    """Render signup UI."""
    qs = st.query_params.to_dict()
    qs_email = qs["email"][0] if "email" in qs else None
    qs_name = qs["name"][0] if "name" in qs else ""

    if system_feature_enabled(SystemFeatureType.FREE_USER_SIGNUP, show_message=False) or qs_email:
        _ctx = ExtensionContext(data={"qs_email": qs_email, "qs_name": qs_name})

        handle_fire_extensions_callbacks("webui.signup_ui.render_started", _ctx)

        _disable_sidebar()
        handle_logout()
        st.title("Docq Signup")
        st.markdown('Already have an account? Login <a href="/" target="_self">here</a>.', unsafe_allow_html=True)

        if not handle_check_mailer_ready():
            log.error(
                "Mailer service not available due to a config problem. User self signup disabled. All the following env vars needs to be set: DOCQ_SMTP_SERVER, DOCQ_SMTP_PORT, DOCQ_SMTP_LOGIN, DOCQ_SMTP_KEY, DOCQ_SMTP_FROM, DOCQ_SERVER_ADDRESS. Refer to he `misc/secrets.toml.template` in the repo for details."
            )
            st.error("Unable to create personal accounts.")
            st.info("Please contact your administrator to help you create an account.")
            st.stop()

        form = "user-signup"
        st.session_state[f"{form}-validator"] = st.empty()

        with st.form(key=form):
            st.text_input("Name", placeholder="Bob Smith", key=f"{form}-name", value=qs_name, autocomplete="name")
            st.text_input(
                "Email",
                placeholder="bob.smith@acme.com",
                key=f"{form}-email",
                value=qs_email,
                disabled=qs_email is not None,
                autocomplete="email",
            )
            st.text_input(
                "Password",
                type="password",
                key=f"{form}-password",
                help="Password must be at least 8 characters long and contain at least 1 lowercase letter, 1 uppercase letter, 1 number and 1 special character.",
                autocomplete="new-password",
            )
            submit = st.form_submit_button("Signup")
            if submit:
                handle_fire_extensions_callbacks("webui.sign_ui.form.submitted", _ctx)
                validate_signup_form()
                handle_user_signup()

        if st.session_state.get(f"{form}-resend-verification-email", False):
            with st.session_state[f"{form}-validator"].container():
                __resend_verification_ui(st.session_state[f"{form}-email"], form)

        handle_fire_extensions_callbacks("webui.sign_ui.render_completed", _ctx)


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


def render_integrations() -> None:
    """Render integrations."""
    teams = handle_list_slack_installations()
    team: Optional[SlackInstallation] = st.selectbox(
        "Select a slack team",
        options=teams,
        format_func=lambda x: x.team_name,
        key="selected_slack_team"
    )

    st.divider()
    st.write("### Channels")

    if team is not None:
        channels = handle_list_slack_channels(team.app_id, team.team_id)
        space_groups = list_space_groups()

        print(f"\x1b[31mDebug team: {team.team_id}\nchannels: {channels}\x1b[0m")
        for channel in channels:
            with st.expander(f"### {channel['name']}"):
                st.write(channel['purpose']['value'])
                st.selectbox(
                    "Select a space group",
                    options=space_groups,
                    format_func=lambda x: x[2],
                    key=f"selected_space_group_{channel['id']}",
                    index=None
                )
                _, save_btn, _ = st.columns([1, 1, 1])
                save_btn.button("Save Space Group Selection", key=f"save_selected_space_group_:{channel['id']}")

        if not channels:
            st.info("No slack channels found")
    else:
        st.info("No slack teams found")


def render_slack_installation_button() -> None:
    """Render slack installation button."""
    _, center, _ = st.columns([1, 1, 1])
    with center:
        if st.button("Install Docq Slack Application", type="primary"):
            handle_install_docq_slack_application()
