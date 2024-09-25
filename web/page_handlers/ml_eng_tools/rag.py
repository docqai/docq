"""ML Eng - Visualise index."""

import logging as log
import os
from typing import List

import streamlit as st
from docq.config import SpaceType
from docq.data_source.list import SpaceDataSources
from docq.domain import Assistant, SpaceKey
from docq.manage_spaces import get_space_data_source, list_space
from docq.model_selection.main import LlmUsageSettingsCollection, ModelCapability, get_saved_model_settings_collection
from docq.support.llama_index.node_post_processors import reciprocal_rank_fusion
from docq.support.llm import _get_service_context
from docq.support.rag_pipeline import rag_pipeline
from docq.support.store import (
    _get_path,
    _map_space_type_to_datascope,
    _StoreDir,
)
from llama_index.core import VectorStoreIndex
from llama_index.core.base.response.schema import Response
from llama_index.core.indices import load_index_from_storage
from llama_index.core.indices.base import BaseIndex
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.schema import BaseNode, Document, NodeWithScore
from llama_index.core.storage import StorageContext
from llama_index.retrievers.bm25 import BM25Retriever
from page_handlers.ml_eng_tools.visualise_index import visualise_vector_store_index
from streamlit.delta_generator import DeltaGenerator
from utils.layout import auth_required, render_page_title_and_favicon
from utils.sessions import get_selected_org_id

render_page_title_and_favicon(layout="wide")
auth_required(requiring_selected_org_admin=True)

above_tabs_container = st.container()
left_col, right_col = st.columns(2)
chat_tab, index_tab = left_col.tabs(["chat_tab", "index_tab"])


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
above_tabs_container.write(f"Experiment ID: `{experiment_id}` within Org ID: `{selected_org_id}`")
above_tabs_container.write(
    f"All index creation and loading is contained withing a sub dir called `exp_{experiment_id}`"
)


spaces = []
selected_space = None
if selected_org_id:
    spaces.extend(list_space(selected_org_id, SpaceType.SHARED.name))
    spaces.extend(list_space(selected_org_id, SpaceType.THREAD.name))
    # list_shared_spaces(org_id=selected_org_id)
    selected_space = above_tabs_container.selectbox(
        "Space",
        spaces,
        format_func=lambda x: x[2],
        label_visibility="visible",
        index=0,
        key="selected_space",
    )


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
    ch = st.session_state.get(f"rag_test_chat_history_content_{selected_space_key.id_}", None)
    if not ch:
        st.session_state[f"rag_test_chat_history_content_{selected_space_key.id_}"] = [
            ChatMessage(role=MessageRole.ASSISTANT, content="Hello, ask me a question.")
        ]


with chat_tab:
    prepare_chat()


def render_retrieval_query_ui(container: DeltaGenerator):
    persona = Assistant(
        "Assistant",
        "Assistant",
        "You are a helpful AI assistant. Only use the provided context to answer the query.",
        "{query_str}",
        "",
    )
    from llama_index.core.retrievers import QueryFusionRetriever
    from llama_index.core.retrievers.fusion_retriever import FUSION_MODES

    vector_retriever = index_.as_retriever(similarity_top_k=4)

    bm25_retriever = BM25Retriever.from_defaults(docstore=index_.docstore, similarity_top_k=4)
    retriever = QueryFusionRetriever(
        [vector_retriever, bm25_retriever],
        similarity_top_k=4,
        num_queries=4,  # set this to 1 to disable query generation
        mode=FUSION_MODES.RECIPROCAL_RANK,
        use_async=False,
        verbose=True,
        llm=_get_service_context(saved_model_settings).llm,
        # query_gen_prompt="...",  # we could override the query generation prompt here
    )

    container.write("Ask a question to retrieve documents from the index.")
    container.text_area("Query", key="retrieval_query_rag_test", value="who are the cofounders fo Docq?")
    retrieve_button = container.button("Retrieve")

    if retrieve_button:
        query = st.session_state.get("retrieval_query_rag_test", None)
        if query:
            # query_embed = _get_service_context(saved_model_settings).embed_model.get_query_embedding(query)
            # query_bundle = QueryBundle(query_str=query, custom_embedding_strs=query, embedding=query_embed)
            # ret_results = engine.retrieve(query_bundle)
            ret_results = retriever.retrieve(query)
            # resp = engine.query(query)
            # print("ret_results: ", ret_results)

            render_retreival_results(ret_results)


def render_retreival_results(results: List[NodeWithScore]):
    st.write("Retrieved Chunks:")
    for node in results:
        with st.expander(node.node_id):
            st.write(node)


def handle_chat_input():
    """Handle chat input."""
    if not index_:
        st.error("Index not loaded. Please select a space and load the index first.")
        return

    space_indices = [index_]

    persona = Assistant(
        "Assistant",
        "Assistant",
        "You are a helpful AI assistant. Do not previous knowledge. Only use the provided context to answer the query.",
        "{query_str}",
        "",
    )
    # engine = index_.as_query_engine(
    #     llm=_get_service_context(saved_model_settings).llm,
    #     text_qa_template=llama_index_chat_prompt_template_from_persona(persona).partial_format(history_str=""),
    # )

    # from llama_index.core.retrievers import QueryFusionRetriever
    # from llama_index.core.retrievers.fusion_retriever import FUSION_MODES

    # vector_retriever = index_.as_retriever(similarity_top_k=10)

    # bm25_retriever = BM25Retriever.from_defaults(docstore=index_.docstore, similarity_top_k=10)
    # retriever = QueryFusionRetriever(
    #     [vector_retriever, bm25_retriever],
    #     similarity_top_k=5,
    #     num_queries=4,  # set this to 1 to disable query generation
    #     mode=FUSION_MODES.RECIPROCAL_RANK,
    #     use_async=False,
    #     verbose=True,
    #     llm=_get_service_context(saved_model_settings).llm,
    #     # query_gen_prompt="...",  # we could override the query generation prompt here
    # )

    # from llama_index.core.query_engine import RetrieverQueryEngine

    # query_engine = RetrieverQueryEngine.from_args(
    #     retriever,
    #     service_context=_get_service_context(saved_model_settings),
    #     text_qa_template=llama_index_chat_prompt_template_from_assistant(persona).partial_format(history_str=""),  # noqa: F821
    # )

    chat_history: List[ChatMessage] = st.session_state.get(
        f"rag_test_chat_history_content_{selected_space_key.id_}", []
    )

    print("chat_history: ", chat_history)

    query = st.session_state.get("chat_input_rag_test", None)
    if query:
        # query_embed = _get_service_context(saved_model_settings).embed_model.get_query_embedding(query)
        # query_bundle = QueryBundle(query_str=query, custom_embedding_strs=query, embedding=query_embed)
        # ret_results = query_engine.retrieve(query_bundle)
        # resp = query_engine.query(query)

        resp = rag_pipeline(
            user_query=query,
            indices=space_indices,
            assistant=persona,
            message_history=chat_history,
            llm=_get_service_context(saved_model_settings).llm,
            reranker=lambda results: reciprocal_rank_fusion(results),
            query_preprocessor=None,
            top_k=6,
        )

        if isinstance(resp, Response):
            # st.session_state[f"rag_test_chat_history_content_{selected_space_key.id_}"].extend([query, resp.response])
            st.session_state[f"rag_test_chat_history_content_{selected_space_key.id_}"].extend(
                [
                    ChatMessage(role=MessageRole.USER, content=query),
                    ChatMessage(role=MessageRole.ASSISTANT, content=resp.response),
                ]
            )


def render_chat():
    # st.write(st.session_state.get("chat_input_rag_test", "Hello, ask a questions."))
    chat_history: list[ChatMessage] = st.session_state.get(
        f"rag_test_chat_history_content_{selected_space_key.id_}", []
    )
    for cm in chat_history:
        st.write(f"{cm.role}: {cm.content}")

    st.chat_input(
        "Type your question here",
        key="chat_input_rag_test",
        on_submit=handle_chat_input,
    )


def clear_chat():
    st.session_state[f"rag_test_chat_history_content_{selected_space_key.id_}"] = []


if index_:
    render_retrieval_query_ui(above_tabs_container)

with chat_tab:
    st.button("Clear Chat", on_click=clear_chat)

    render_chat()
