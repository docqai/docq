from datetime import datetime
import streamlit as st
from streamlit_chat import message

from .constants import SessionKeyName, SpaceType, MAX_NUMBER_OF_DOCS, ALLOWED_DOC_EXTS
from .utils import *


def chat_ui(type_: SpaceType):
    with st.container():
        if st.button('Load chat history earlier'):
            query_history(type_)
        day = format_datetime(get_session_state(type_, SessionKeyName.CUTOFF))
        st.markdown(f"#### {day}")
        for key, text, is_user, time in get_session_state(type_, SessionKeyName.HISTORY):
            if format_datetime(time) != day:
                day = format_datetime(time)
                st.markdown(f"#### {day}")
            message(text, is_user, key=key)

    st.divider()
    st.text_input("Type your question here", value='', key=f'chat_input_{type_}', on_change=handle_chat_input, args=(type_,))


def documents_ui(type_: SpaceType):
    documents = list_documents(type_)
    if documents:
        for i, (filename, time, size) in enumerate(documents):
            with st.expander(filename):
                st.markdown(f"Size: {format_filesize(size)} | Time: {format_datetime(datetime.fromtimestamp(time))}")
                st.button('Delete', key=f'delete_file_{i}_{type_}', on_click=delete_document, args=(filename, type_))
        st.button('Delete all documents', key=f'delete_all_files_{type_}', on_click=delete_all_documents, args=(type_,))

    st.divider()

    if len(documents) < MAX_NUMBER_OF_DOCS:
        with st.form("Upload", clear_on_submit=True):
            st.file_uploader("Upload your documents here", type=ALLOWED_DOC_EXTS, key=f'uploaded_file_{type_}')
            st.form_submit_button(label='Upload', on_click=handle_upload_file, args=(type_,))
    else:
        st.warning(f"You cannot upload more than {MAX_NUMBER_OF_DOCS} documents.")



def spaces_ui(type_: SpaceType):
    spaces = list_spaces(type_)
    if spaces:
        for name, summary in spaces:
            with st.expander(name):
                st.write(summary)