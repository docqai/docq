from datetime import datetime
from typing import Optional, Any
import streamlit as st
import logging

from docq import ask, config, manage

from .constants import SESSION_KEY_NAME_DOCQ, SessionKeyName, SpaceType


def get_session_state(type_: Optional[SpaceType] = None, key_: Optional[SessionKeyName] = None) -> Any:
    if type_ is None and key_ is None:
        return st.session_state[SESSION_KEY_NAME_DOCQ]
    elif key_ is None:
        return st.session_state[SESSION_KEY_NAME_DOCQ][type_.value]
    else:
        return st.session_state[SESSION_KEY_NAME_DOCQ][type_.value][key_.value]


def set_session_state(val: Any, type_: Optional[SpaceType] = None, key_: Optional[SessionKeyName] = None) -> None:
    if type_ is None and key_ is None:
        st.session_state[SESSION_KEY_NAME_DOCQ] = val
    elif key_ is None:
        st.session_state[SESSION_KEY_NAME_DOCQ][type_.value] = val
    else:
        st.session_state[SESSION_KEY_NAME_DOCQ][type_.value][key_.value] = val


def query_history(type_: SpaceType):
    curr_cutoff = get_session_state(type_, SessionKeyName.CUTOFF)
    history = ask.history(curr_cutoff, config.ASK_LOAD_NUMBER_OF_MESSAGES, type_.value)
    set_session_state(history + get_session_state(type_, SessionKeyName.HISTORY), type_, SessionKeyName.HISTORY)
    set_session_state(history[0][3] if history else curr_cutoff, type_, SessionKeyName.CUTOFF)


def handle_chat_input(type_: SpaceType):
    now = datetime.now()
    req = st.session_state[f'chat_input_{type_}']
    get_session_state(type_, SessionKeyName.HISTORY).append((f"{type_}-{now}-req", now, req, True))
    res = ask.question(req, type_.value)
    then = datetime.now()
    get_session_state(type_, SessionKeyName.HISTORY).append((f"{type_}-{then}-res", res.response if res.response else "Sorry I don't have enough data to answer this question.", False, then))
    st.session_state[f'chat_input_{type_}'] = ''


def list_documents(type_: SpaceType):
    return manage.show(type_.value)


def delete_document(filename: str, type_: SpaceType, ):
    manage.delete(filename, type_.value)


def delete_all_documents(type_: SpaceType):
    manage.delete_all(type_.value)


def handle_upload_file(type_: SpaceType):
    manage.upload(st.session_state[f'uploaded_file_{type_}'], type_.value)


def list_spaces(type_: SpaceType):
    return [('a shared space', 'organisational data store, updated frequently')]


def format_datetime(dt):

    if isinstance(dt, datetime):
        res = dt.strftime("%Y-%m-%d")
    elif isinstance(dt, str):
        res = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
    else:
        logging.warning(f"Failed to format datetime so returning as is.")
        res = dt
    return res


def format_filesize(size):
    return f"{round(size / 1024 / 1024, 1)} Mb"


def init(type_: SpaceType):

    if '_docq' not in st.session_state:
        set_session_state({})

    if type_ not in get_session_state():
        set_session_state({}, type_)

    if 'cutoff' not in get_session_state(type_):
        set_session_state(datetime.now(), type_, SessionKeyName.CUTOFF)

    if 'history' not in get_session_state(type_):
        set_session_state([], type_, SessionKeyName.HISTORY)

    if not get_session_state(type_, SessionKeyName.HISTORY):
        query_history(type_)
        if not get_session_state(type_, SessionKeyName.HISTORY):
            set_session_state([('0', 'Hi there! This is Docq, ask me anything.', False, datetime.now())], type_, SessionKeyName.HISTORY)
