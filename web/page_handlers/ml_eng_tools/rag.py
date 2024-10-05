"""ML Eng - Visualise index."""

import json
import logging as log
import os
from typing import Any, List, Tuple

import streamlit as st
from docq.config import SpaceType
from docq.data_source.list import SpaceDataSources
from docq.domain import SpaceKey
from docq.manage_assistants import list_assistants
from docq.manage_spaces import get_space_data_source, list_space
from docq.model_selection.main import LlmUsageSettingsCollection, ModelCapability, get_saved_model_settings_collection
from docq.support.llama_index.node_post_processors import reciprocal_rank_fusion
from docq.support.llm import _get_service_context
from docq.support.rag_pipeline import generation_stage, search_stage
from docq.support.store import (
    _DataScope,
    _get_path,
    _map_space_type_to_datascope,
    _StoreDir,
)
from llama_index.core import VectorStoreIndex
from llama_index.core.indices import load_index_from_storage
from llama_index.core.indices.base import BaseIndex
from llama_index.core.llms import ChatMessage, ChatResponse, MessageRole
from llama_index.core.schema import BaseNode, Document, NodeWithScore
from llama_index.core.storage import StorageContext
from page_handlers.ml_eng_tools.visualise_index import visualise_vector_store_index
from utils.layout import auth_required, render_page_title_and_favicon
from utils.layout_assistants import (
    render_assistant_create_edit_ui,
    render_assistants_selector_ui,
    render_datascope_selector_ui,
)
from utils.sessions import get_selected_org_id

render_page_title_and_favicon(layout="wide")
auth_required(requiring_selected_org_admin=True)

top_container = st.container()

above_tabs_container = st.container()
above_left_col, above_right_col = above_tabs_container.columns(2)


left_col, right_col = st.columns(2)
chat_tab, index_tab, assistant_tab = left_col.tabs(["Chat", "Vec Index", "Assistant"])
stuff_tab, search_results_tab = right_col.tabs(["stuff", "search_results"])

# select a live space
# create an experimental index
# chat with space over experimental index (no saved threads, clear the chat)
# iterate on the assist prompt
# visualise the retrieved chunks for a chat
# layout chat and assist prompt on the left. visualise the retrieved chunks on the right


def _get_experiement_dir(space: SpaceKey, experiment_id: str) -> str:
    return _get_path(
        store=_StoreDir.INDEX,
        data_scope=_map_space_type_to_datascope(space.type_),
        subtype=os.path.join(str(space.org_id), "exp_" + str(experiment_id), str(space.id_)),
    )


def _get_experiments_storage_context(space: SpaceKey, experiment_id: str) -> StorageContext:
    return StorageContext.from_defaults(persist_dir=_get_experiement_dir(space, experiment_id))


def _load_experiment_index_from_storage(
    space: SpaceKey, model_settings_collection: LlmUsageSettingsCollection, exp_id: str
) -> BaseIndex:
    """Load index from storage."""
    storage_context = _get_experiments_storage_context(space, exp_id)  # _get_storage_context(space)
    service_context = _get_service_context(model_settings_collection)
    return load_index_from_storage(storage_context=storage_context, service_context=service_context)


def _load_vector_store_index(
    space: SpaceKey, model_settings_collection: LlmUsageSettingsCollection, exp_id: str
) -> VectorStoreIndex:
    """Load index from storage."""
    storage_context = _get_experiments_storage_context(space, exp_id)
    service_context = _get_service_context(model_settings_collection)
    return VectorStoreIndex.from_vector_store(storage_context.vector_store, service_context=service_context)


def _create_vector_index(
    documents: list[Document], model_settings_collection: LlmUsageSettingsCollection, space: SpaceKey, exp_id: str
) -> VectorStoreIndex:
    # Use default storage and service context to initialise index purely for persisting
    sc = _get_service_context(model_settings_collection)
    # nodes = get_nodes_from_documents(documents)

    # index_ = VectorStoreIndex(
    #     nodes=nodes,
    #     service_context=_get_service_context(model_settings_collection),
    #     storage_context=_get_default_storage_context(),
    # )
    # VectorStoreIndex.build_index_from_nodes(index_, nodes=nodes)
    log.debug("service context: ", sc.embed_model)
    index_ = VectorStoreIndex.from_documents(
        documents,
        storage_context=_get_experiments_storage_context(space, exp_id),
        service_context=sc,
        show_progress=True,
        kwargs=model_settings_collection.model_usage_settings[ModelCapability.EMBEDDING].additional_args,
    )
    return index_


def load_documents_from_space(space: SpaceKey) -> list[Document] | None:
    """Load documents from space."""
    _space_data_source = get_space_data_source(selected_space_key)

    if _space_data_source is None:
        raise ValueError(f"No data source found for space.")

    (ds_type, ds_configs) = _space_data_source

    space_data_source = SpaceDataSources[ds_type].value

    docs = space_data_source.load(selected_space_key, ds_configs)

    return docs


def get_nodes_from_documents(docs: list[Document]) -> list[BaseNode]:
    nodes = []
    for doc in docs:
        if doc.child_nodes:
            for node in doc.child_nodes:
                nodes.append(node.copy())
    return nodes


def render_documents(docs: list[Document]):
    for doc in docs:
        with st.expander(doc.doc_id):
            st.write(doc)


experiment_id = "sasdfasdf"
selected_org_id = get_selected_org_id()
with top_container:
    st.write(f"Experiment ID: `{experiment_id}` within Org ID: `{selected_org_id}`")
    st.write(f"All index creation and loading is contained withing a sub dir called `exp_{experiment_id}`")


spaces = []
selected_space = None
if selected_org_id:
    spaces.extend(list_space(selected_org_id, SpaceType.SHARED.name))
    spaces.extend(list_space(selected_org_id, SpaceType.THREAD.name))
    # list_shared_spaces(org_id=selected_org_id)
    selected_space = above_left_col.selectbox(
        "Space",
        spaces,
        format_func=lambda x: x[2],
        label_visibility="visible",
        index=0,
        key="selected_space",
    )

selected_assistant = None
with above_right_col:
    datascope = render_datascope_selector_ui()
    current_org_id = None
    if datascope == _DataScope.ORG:
        current_org_id = get_selected_org_id()
        if current_org_id is None:
            st.error("Please select an organisation")
            st.stop()
        st.write(f"Selected Organisation: {current_org_id}")

    assistants_data = list_assistants(org_id=current_org_id)

    selected_assistant = render_assistants_selector_ui(assistants_data=assistants_data)

    if selected_assistant:
        with assistant_tab:
            render_assistant_create_edit_ui(org_id=current_org_id, assistant_data=selected_assistant)


if selected_space and selected_org_id:
    log.debug("selected_space: ", selected_space)

    selected_space_key = SpaceKey(
        type_=SpaceType[selected_space[7]], id_=selected_space[0], org_id=selected_org_id, summary=selected_space[2]
    )

    saved_model_settings = get_saved_model_settings_collection(selected_org_id)

    docs = load_documents_from_space(selected_space_key)

    if not docs:
        above_tabs_container.write("No documents found in the Space.")
        st.stop()

    index_ = None
    try:
        # index_ = _load_vector_store_index(selected_space_key, saved_model_settings, experiment_id)
        index_ = _load_experiment_index_from_storage(selected_space_key, saved_model_settings, experiment_id)
    except Exception as e:
        above_tabs_container.write("No index. Index the space first.")
        print(e)

    IndexSpaceButton = above_tabs_container.button("Index Space")

    if IndexSpaceButton:
        # storage_context = _get_default_storage_context()  # get a storage content.
        log.debug("models: ", saved_model_settings)
        index_ = _create_vector_index(docs, saved_model_settings, selected_space_key, experiment_id)
        # storage_context.persist(persist_dir=_get_experiement_dir(selected_space_key, experiment_id))
        index_.storage_context.persist()  # persist to the experiment dir
        # index_.storage_context.persist(persist_dir=_get_experiement_dir(selected_space_key, experiment_id))

    with index_tab:
        if index_ and isinstance(index_, VectorStoreIndex):
            visualise_vector_store_index(index_)


def prepare_chat():
    ch = st.session_state.get(f"rag_test_chat_history_content_{selected_space_key.id_}", [])
    if not ch:
        st.session_state[f"rag_test_chat_history_content_{selected_space_key.id_}"] = [
            (ChatMessage(role=MessageRole.ASSISTANT, content="Hello, ask me a question."), None)
        ]


with chat_tab:
    prepare_chat()


def render_retrieval_results(results: List[NodeWithScore]):
    st.write("Retrieved Chunks:")
    for node in results:
        node_json = json.loads(node.to_json())
        with st.expander(node.node_id):
            st.write(node_json)


def handle_chat_input():
    """Handle chat input."""
    if not index_:
        st.error("Index not loaded. Please select a space and load the index first.")
        return

    space_indices = [index_]

    if selected_assistant:
        persona = selected_assistant

    # persona = Assistant(
    #     "Assistant",
    #     "Assistant",
    #     "You are a helpful AI assistant. Do not use previous knowledge to answer queries. Only use the provided context to answer the query. If you cannot provide a reasonable answer based on the given context and message history then say 'Sorry, I cannot provide an answer to that question.'",
    #     "context: {context_str}\nquery: {query_str}",
    #     "",
    # )

    chat_messages: List[Tuple[ChatMessage, Any]] = st.session_state.get(
        f"rag_test_chat_history_content_{selected_space_key.id_}", []
    )

    chat_history = [cm[0] for cm in chat_messages]

    query = st.session_state.get("chat_input_rag_test", None)
    if query and persona:
        # query_embed = _get_service_context(saved_model_settings).embed_model.get_query_embedding(query)
        # query_bundle = QueryBundle(query_str=query, custom_embedding_strs=query, embedding=query_embed)
        # ret_results = query_engine.retrieve(query_bundle)
        # resp = query_engine.query(query)

        search_results, search_debug = search_stage(
            user_query=query, indices=space_indices, reranker=reciprocal_rank_fusion, top_k=6
        )

        resp, gen_debug = generation_stage(
            user_query=query,
            assistant=persona,
            search_results=search_results,
            message_history=chat_history,
            llm=_get_service_context(saved_model_settings).llm,
            enable_debug=True,
        )

        # resp = rag_pipeline(
        #     user_query=query,
        #     indices=space_indices,
        #     assistant=persona,
        #     message_history=chat_history,
        #     llm=_get_service_context(saved_model_settings).llm,
        #     reranker=lambda results: reciprocal_rank_fusion(results),
        #     query_preprocessor=None,
        #     top_k=6,
        # )

        # with search_results_tab:
        #     render_retrieval_results(search_results)

        if isinstance(resp, ChatResponse):
            # st.session_state[f"rag_test_chat_history_content_{selected_space_key.id_}"].extend([query, resp.response])
            st.session_state[f"rag_test_chat_history_content_{selected_space_key.id_}"].extend(
                [
                    (ChatMessage(role=MessageRole.USER, content=query), None),
                    (ChatMessage(role=MessageRole.ASSISTANT, content=resp.message.content), gen_debug),
                ]
            )


def render_stuff_click_handler(debug) -> None:
    for key, value in debug.items():
        if key == "search_results":
            with search_results_tab:
                render_retrieval_results(value)
        else:
            with stuff_tab.expander(key):
                st.write()
                st.write(value)


def render_chat():
    chat_history: List[Tuple[ChatMessage, Any]] = st.session_state.get(
        f"rag_test_chat_history_content_{selected_space_key.id_}", []
    )

    for i, (cm, debug) in enumerate(chat_history):
        col1, col2 = st.columns(spec=[0.9, 0.1], gap="small")  # Adjust the column width ratios as needed

        with col1:
            st.write(f"{cm.role.name}: {cm.content}")

        with col2:
            if debug:
                st.button(
                    ":bug:",
                    key=f"debug_bt_{i}",
                    on_click=lambda debug=debug: render_stuff_click_handler(debug),
                )

    st.chat_input(
        "Type your question here",
        key="chat_input_rag_test",
        on_submit=handle_chat_input,
    )


def clear_chat():
    st.session_state[f"rag_test_chat_history_content_{selected_space_key.id_}"] = []


with chat_tab:
    st.button("Clear Chat", on_click=clear_chat)

    render_chat()
