from datetime import datetime
import logging as log

import streamlit as st
from docq import ask, config, manage
from st_pages import add_page_title
from streamlit_chat import message


log.basicConfig(level=log.INFO)


def query_history():
    curr_cutoff = st.session_state['chats']['cutoff']
    history = ask.history(curr_cutoff, config.ASK_LOAD_NUMBER_OF_MESSAGES, 'personal')
    log.info("Loaded chat history from %s", curr_cutoff)
    st.session_state['chats']['personal'] = history + st.session_state['chats']['personal']
    st.session_state['chats']['cutoff'] = history[0][1] if history else curr_cutoff


@st.cache_data
def list_documents():
    return manage.show('personal')


def handle_chat_input():
    now = datetime.now()
    req = st.session_state['chat_input']
    st.session_state['chats']['personal'].append((f"{now}-req", now, req, True))
    res = ask.question(req, 'personal')
    log.info("Question: %s, Answer: %s", req, res)
    then = datetime.now()
    st.session_state['chats']['personal'].append((f"{then}-res", then, res, False))
    st.session_state['chat_input'] = ''

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d")

def init():

    if 'chats' not in st.session_state:
        st.session_state['chats'] = {}

    if 'cutoff' not in st.session_state['chats']:
        st.session_state['chats']['cutoff'] = datetime.now()

    if 'personal' not in st.session_state['chats']:
        st.session_state['chats']['personal'] = []

    if not st.session_state['chats']['personal']:
        query_history()
        if not st.session_state['chats']['personal']:
            st.session_state['chats']['personal'] = [('0', datetime.now(), 'Hi there! This is Docq, ask me anything.', False)]


init()

add_page_title()

tab_chat, tab_manage = st.tabs(["Ask Questions", "Manage Documents"])


with tab_chat:
    st.subheader("Ask")

    with st.container():
        if st.button('Load chat history earlier'):
            query_history()
        day = format_datetime(st.session_state['chats']['cutoff'])
        st.markdown(f"### {day}")
        for key, time, text, is_user in st.session_state['chats']['personal']:
            if format_datetime(time) != day:
                day = format_datetime(time)
                st.markdown(f"### {day}")
            message(text, is_user, key=key)

    st.divider()
    chat_input = st.text_input("Type your question here", value='', key='chat_input', on_change=handle_chat_input)


with tab_manage:
    st.subheader("Manage")
    document_list = st.container()
    with document_list:
        for (id, doc) in list_documents():
            document_list.markdown(f"- {doc}")

    uploaded_files = st.file_uploader("Upload your documents here", accept_multiple_files=True)
    for f in uploaded_files:
        manage.upload(f, 'personal')