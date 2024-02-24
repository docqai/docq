"""UI Layout helpers for assistants."""

from typing import Optional

import streamlit as st
from docq.domain import PersonaType
from docq.manage_assistants import ASSISTANT, create_or_update_assistant
from docq.model_selection.main import LLM_MODEL_COLLECTIONS
from docq.support.store import _DataScope
from utils.error_ui import _handle_error_state_ui, set_error_state_for_ui
from utils.validation_ui import _handle_validation_state_ui, set_validation_state_for_ui


def render_assistant_create_edit_ui(org_id: Optional[int] = None, assistant_data: Optional[ASSISTANT] = None, key_suffix: Optional[str] = "new") -> None:
    """Render assistant create/edit form."""
    _handle_error_state_ui(f"assistant_edit_form_error_{key_suffix}")
    with st.form(key=f"assistant_edit_{key_suffix}", clear_on_submit=True):
        button_label = "Create Assistant"
        assistant_id = None
        if assistant_data:
            assistant_id = assistant_data[0]
            button_label = "Update Assistant"
            st.write(f"ID: {assistant_data[0]}")
            st.write(f"Created At: {assistant_data[7]} | Updated At: {assistant_data[8]}")
        _handle_validation_state_ui("assistant_edit_form_name_validation_{key_suffix}")
        st.text_input(
            label="Name",
            placeholder="Assistant 1",
            key=f"assistant_edit_name_{key_suffix}",
            value=assistant_data[1] if assistant_data else None,
        )
        st.selectbox(
            "Type",
            options=[persona_type for persona_type in PersonaType],
            format_func=lambda x: x.value,
            label_visibility="visible",
            key=f"assistant_edit_type_{key_suffix}",
            index=[persona_type.name for persona_type in PersonaType].index(assistant_data[2]) if assistant_data else 1,
        )
        st.text_input(label="System Prompt Template", placeholder="", key=f"assistant_edit_system_prompt_template_{key_suffix}")
        st.text_input(label="User Prompt Template", placeholder="", key=f"assistant_edit_user_prompt_template_{key_suffix}")
        st.selectbox(
            "LLM Settings Collection",
            options=[llm_settings_collection for _, llm_settings_collection in LLM_MODEL_COLLECTIONS.items()],
            format_func=lambda x: x.name,
            label_visibility="visible",
            key=f"assistant_edit_model_settings_collection_{key_suffix}",
        )
        st.text_input(
            label="Space Group ID", placeholder="(Optional) Space group for knowledge", key=f"assistant_edit_space_group_id_{key_suffix}"
        )


        st.form_submit_button(label=button_label, on_click=handle_assistant_create_edit, args=(org_id, assistant_id, key_suffix,))



def render_assistants_selector_ui(assistants_data: list[ASSISTANT]) -> ASSISTANT | None:
    """Render assistants selector and create/edit assistant form."""
    selected = st.selectbox(
        "Assistant",
        options=[assistant for assistant in assistants_data],
        format_func=lambda x: x[1],
        label_visibility="visible",
        index=0,
    )
    return selected


def render_assistants_listing_ui(assistants_data: list[ASSISTANT], org_id: Optional[int] = None) -> None:
    """Render assistants listing."""
    for assistant in assistants_data:
        with st.expander(f"{assistant[1]} ({assistant[0]})", expanded=False):
            st.write(f"ID: {assistant[0]}")
            st.write(f"Created At: {assistant[7]} | Updated At: {assistant[8]}")
            edit = st.button(label="Edit Assistant", key=f"edit_assistant_{assistant[0]}")
            if edit:
                render_assistant_create_edit_ui(org_id=org_id, assistant_data=assistant, key_suffix=str(assistant[0]))


def handle_assistant_create_edit(org_id: Optional[int] = None, assistant_id: Optional[int] = None, key_suffix: Optional[str] = "new") -> None:
    """Handle assistant create/edit form submission."""
    if st.session_state[f"assistant_edit_type_{key_suffix}"] not in PersonaType:
        set_error_state_for_ui(key=f"assistant_edit_form_error_{key_suffix}", error=str(ValueError("Invalid assistant type")), message="Invalid Assistant Type")

    try:
        persona_type: PersonaType = st.session_state[f"assistant_edit_type_{key_suffix}"]

        create_or_update_assistant(
            name=st.session_state[f"assistant_edit_name_{key_suffix}"],
            assistant_type=persona_type,
            system_prompt_template=st.session_state[f"assistant_edit_system_prompt_template_{key_suffix}"],
            user_prompt_template=st.session_state[f"assistant_edit_user_prompt_template_{key_suffix}"],
            llm_settings_collection_key=st.session_state[f"assistant_edit_model_settings_collection_{key_suffix}"].key,
            archived=False,
            org_id=org_id,
            assistant_id=assistant_id,
        )
    except Exception as e:
        if "UNIQUE constraint failed: assistants.name" in e.args:
            set_validation_state_for_ui(
                key=f"assistant_edit_form_name_validation_{key_suffix}",
                error=str(e),
                message="Assistant names must be unique. There's already one with the same name. Please use a different name.",
            )
        else:
            set_error_state_for_ui(key=f"assistant_edit_form_error_{key_suffix}", error=str(e), message="Error saving assistant.")

def render_datascope_selector_ui() -> _DataScope | None:
    """Render data scope selector."""
    return st.selectbox("Data Scope", [_DataScope.ORG, _DataScope.GLOBAL], format_func=lambda x: str(x.value).capitalize(), index=0)
