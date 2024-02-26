"""UI for error handling.

Because Callbacks in Streamlit components don't support try...except blocks, we need to handle errors in a different way.
We use session state pass errors caught in callback handler function to the UI. This is similar to how component values are accessed in the callback.
"""
import logging as log
from typing import Optional

import streamlit as st

from .constants import SESSION_KEY_NAME_ERROR_STATE


def _handle_error_state_ui(key: str, bubble_error_message: bool = True) -> None:
    """Render a pretty error UI.

    if session_state[SESSION_KEY_NAME_ERROR_STATE][key] is set render the error UI.

    The message is prefixed with the text "Something went wrong. ".

    Args:
        key (str): The key of the error state to be handled. Needs to match the key used to set the error state.
        msg (str): The message to show.
        bubble_error_message (bool, optional): Whether to bubble the error message to the user. Defaults to True.
    """
    if (
        SESSION_KEY_NAME_ERROR_STATE in st.session_state
        and key in st.session_state[SESSION_KEY_NAME_ERROR_STATE]
        and st.session_state[SESSION_KEY_NAME_ERROR_STATE][key] is not None
    ):
        err_state = st.session_state[SESSION_KEY_NAME_ERROR_STATE][key]

        log.debug("error_state 1: %s", st.session_state[SESSION_KEY_NAME_ERROR_STATE])
        log.debug("error_state key %s: %s", key, err_state)
        msg = err_state["message"] if "message" in err_state else ""
        err = err_state["error"] if "error" in err_state else ""
        trace_id = err_state["trace_id"] if "trace_id" in err_state else ""
        trace_id_str = f"Trace ID: {trace_id}" if trace_id else ""
        err_str = f"Error: {err}" if bubble_error_message and err else ""
        st.error(f"Something went wrong. {msg} \n\n {err_str} {trace_id_str}")
        del st.session_state[SESSION_KEY_NAME_ERROR_STATE][key]  # reset the error state for this key
        log.debug("error_state 2: %s", st.session_state[SESSION_KEY_NAME_ERROR_STATE])


def set_error_state_for_ui(key: str, error: str, message: str, trace_id: Optional[str] = None) -> None:
    """Set the UI error state.

    Args:
        key (str): A unique key to identify error state to be handled. Used by _handle_error_ui() to identify the specific error state to be handled.
        error (str): Typically set to the error return by the exception handler. E.g. `error=str(e)` or `error=str(ValueError("bla bla value missing."))`.
        message (str): A user-friendly message to be shown to the user.
        trace_id (Optional[str]): A unique id that identifies this instance of the error.
    """
    st.session_state[SESSION_KEY_NAME_ERROR_STATE] = {
        key: {
            "error": error,
            "message": message,
            "trace_id": trace_id,
        }
    }
