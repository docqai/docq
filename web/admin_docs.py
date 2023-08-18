"""Page: Admin / Manage Documents."""

from typing import Literal

import streamlit as st
from docq.config import SpaceType
from docq.domain import SpaceKey
from st_pages import add_page_title
from utils.handlers import list_shared_spaces
from utils.layout import auth_required, create_space_ui, documents_ui, show_space_details_ui

auth_required(requiring_admin=True)

add_page_title()

PARAM_NAME = "sid"

st.write("""
<style>
    .element-container .row-widget.stSelectbox label {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

def _editor_view(action: str = None) -> None:
    if action == "create":
        st.experimental_set_query_params(**{PARAM_NAME: None})
        create_space_ui(True)

    elif PARAM_NAME in st.experimental_get_query_params():
        space = SpaceKey(SpaceType.SHARED, int(st.experimental_get_query_params()[PARAM_NAME][0]))

        tab_spaces, tab_docs, tab_edit = st.tabs(["Space Details", "Manage Documents", "Edit Space"])

        with tab_docs:
            documents_ui(space)

        with tab_spaces:
            show_space_details_ui(space)

        with tab_edit:
            st.write("Edit space")


st.subheader("Select a space from below:")

list_space, create_space = st.columns([5, 1])

spaces = list_shared_spaces()

def _select_operation(action: Literal["edit"] | Literal["create"]) -> None:
    st.session_state['admin_docs_ctrl'] = action

with list_space:
    selected = st.selectbox("Spaces", spaces, format_func=lambda x: x[1])

with create_space:
    st.button("New Space", on_click=_select_operation, args=("create",))

ctrl = st.session_state.get('admin_docs_ctrl', "edit")
if ctrl == "edit" and selected:
    st.experimental_set_query_params(**{PARAM_NAME: selected[0]})
    _editor_view()
elif ctrl == "create":
    print(f"\x1b[31mDebug: {st.session_state}\x1b[0m")
    _editor_view("create")
