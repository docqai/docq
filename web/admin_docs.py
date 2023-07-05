"""Page: Admin / Manage Documents."""

import streamlit as st
from docq.config import SpaceType
from docq.domain import SpaceKey
from st_pages import add_page_title
from utils.handlers import list_shared_spaces
from utils.layout import auth_required, documents_ui_shared, show_space_details_ui

auth_required(requiring_admin=True)

add_page_title()

PARAM_NAME = "sid"

spaces = list_shared_spaces()
selected = st.selectbox("Selected Space:", spaces, format_func=lambda x: x[1])
if selected:
    st.experimental_set_query_params(**{PARAM_NAME: selected[0]})


if PARAM_NAME in st.experimental_get_query_params():
    space = SpaceKey(SpaceType.SHARED, int(st.experimental_get_query_params()[PARAM_NAME][0]))

    tab_spaces, tab_docs = st.tabs(["Space Details", "Manage Documents"])

    with tab_docs:
        documents_ui_shared(space)

    with tab_spaces:
        show_space_details_ui(space)

