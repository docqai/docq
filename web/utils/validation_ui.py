"""UI for validation handling.

Because Callbacks in Streamlit components don't support try...except blocks, we need to handle validation in a different way.
We use session state to pass validation failures caught in a callback handler function back to the UI. This is similar to how component values are accessed in the callback.
"""
import logging as log
from typing import Optional

import streamlit as st

from .constants import SESSION_KEY_NAME_FORM_VALIDATION_STATE


def _handle_validation_state_ui(key: str, bubble_error_message: Optional[bool] = False) -> None:
    """Render a pretty Validation error UI.

    if session_state[SESSION_KEY_NAME_FORM_VALIDATION_STATE][key] is set render the validation UI.

    The message is prefixed with the text "Something went wrong. ".

    Args:
        key (str): The key of the error state to be handled. Needs to match the key used to set the error state.
        msg (str): The message to show.
        bubble_error_message (Optional[bool]): Whether to bubble the error message to the user. Defaults to False.
    """
    if (
        SESSION_KEY_NAME_FORM_VALIDATION_STATE in st.session_state
        and key in st.session_state[SESSION_KEY_NAME_FORM_VALIDATION_STATE]
        and st.session_state[SESSION_KEY_NAME_FORM_VALIDATION_STATE][key] is not None
    ):
        validation_state = st.session_state[SESSION_KEY_NAME_FORM_VALIDATION_STATE][key]

        log.debug("validation_state 1: %s", st.session_state[SESSION_KEY_NAME_FORM_VALIDATION_STATE])
        log.debug("validation_state key %s: %s", key, validation_state)
        msg = validation_state["message"] if "message" in validation_state else ""
        err = validation_state["error"] if "error" in validation_state else ""
        # trace_id = validation_state["trace_id"] if "trace_id" in validation_state else ""
        # trace_id_str = f"Trace ID: {trace_id}" if trace_id else ""
        err_str = f"Validation error: {err}" if bubble_error_message and err else ""
        st.warning(f"{msg} \n\n{err_str}")
        del st.session_state[SESSION_KEY_NAME_FORM_VALIDATION_STATE][key]  # reset the error state for this key
        log.debug("error_state 2: %s", st.session_state[SESSION_KEY_NAME_FORM_VALIDATION_STATE])


def set_validation_state_for_ui(key: str, error: str, message: str) -> None:
    """Set the UI validation state.

    Args:
        key (str): A unique key to identify validation state to be handled. Used by _handle_validation_ui() to identify the specific validation state to be handled.
        error (str): Validation error details. This value is rendered in the UI if `bubble_error_message` is True.
        message (str): A user-friendly message shown to the user.
    """
    st.session_state[SESSION_KEY_NAME_FORM_VALIDATION_STATE] = {
        key: {
            "error": error,
            "message": message,
        }
    }
