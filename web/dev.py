"""Page: Dev"""

import asyncio
import logging
import os
from typing import List, Sequence

import streamlit as st
from docq.config import ENV_VAR_DOCQ_DATA, SpaceType
from docq.data_source.list import SpaceDataSources
from docq.data_source.main import SpaceDataSource
from docq.domain import SpaceKey
from docq.manage_spaces import get_space_data_source
from docq.model_selection.main import ModelUsageSettingsCollection, get_saved_model_settings_collection
from docq.support.llm import (
    _get_chat_model,
    _get_completion_model,
    _get_llm_predictor,
    _get_service_context,
    _get_storage_context,
    _load_index_from_storage,
)
from docq.support.store import _get_path, _StoreSubdir
from llama_index import (
    Document,
    DocumentSummaryIndex,
    StorageContext,
    VectorStoreIndex,
    get_response_synthesizer,
    load_index_from_storage,
)
from llama_index.evaluation import RetrieverEvaluator
from llama_index.llms import AzureOpenAI
from llama_index.query_engine import BaseQueryEngine, RetrieverQueryEngine
from llama_index.response_synthesizers.type import ResponseMode
from llama_index.retrievers import VectorIndexRetriever
from llama_index.schema import TextNode
from st_pages import add_page_title
from utils.handlers import list_shared_spaces
from utils.layout import auth_required
from utils.sessions import get_selected_org_id

auth_required(requiring_admin=True)

add_page_title()


def _get_exp_path(store: _StoreSubdir, type_: SpaceType, subtype: str = None, filename: str = None) -> str:
    logging.debug("_get_path() - store: %s, type_: %s, subtype: %s, filename: %s", store, type_, subtype, filename)
    dir_ = (
        os.path.join(os.environ[ENV_VAR_DOCQ_DATA], "exp", store.value, type_.name, subtype)
        if subtype
        else os.path.join(os.environ[ENV_VAR_DOCQ_DATA], "exp", store.value, type_.name)
    )
    os.makedirs(dir_, exist_ok=True)
    if filename:
        file_ = os.path.join(dir_, filename)
        logging.debug("File: %s", file_)
        return file_
    else:
        logging.debug("Dir: %s", dir_)
        return dir_


def get_exp_index_dir(space: SpaceKey, exp_id: str) -> str:
    """Get the index directory for a space."""
    return (
        _get_exp_path(store=_StoreSubdir.INDEX, type_=space.type_, subtype=str(space.id_))
        if space.type_ == SpaceType.PERSONAL
        else _get_exp_path(
            store=_StoreSubdir.INDEX,
            type_=space.type_,
            subtype=os.path.join(str(space.org_id), str(space.id_), exp_id),
        )
    )


def _get_exp_storage_context(space: SpaceKey, exp_id: str) -> StorageContext:
    return StorageContext.from_defaults(persist_dir=get_exp_index_dir(space, exp_id))


def load_index(
    space: SpaceKey, model_settings_collection: ModelUsageSettingsCollection, exp_id: str = None
) -> VectorStoreIndex:
    """Load index from storage."""
    storage_context = _get_storage_context(space) if exp_id is None else _get_exp_storage_context(space, exp_id)
    return load_index_from_storage(
        storage_context=storage_context, service_context=_get_service_context(model_settings_collection)
    )


def custom_query_engine(vector_store_index: VectorStoreIndex) -> BaseQueryEngine:
    """Custom query engine."""
    # index = VectorStoreIndex.from_documents(documents)

    # configure retriever
    retriever = VectorIndexRetriever(
        index=vector_store_index,
        similarity_top_k=5,
    )

    # configure response synthesizer
    response_synthesizer = get_response_synthesizer(
        response_mode=ResponseMode.TREE_SUMMARIZE,
        service_context=vector_store_index.service_context,
    )

    # assemble query engine
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
    )
    return query_engine


def get_space_document_objects(space: SpaceKey) -> List[Document]:
    """Get space document objects."""
    (ds_type, ds_configs) = get_space_data_source(space)
    documents = []
    try:
        documents = SpaceDataSources[ds_type].value.load(space, ds_configs)

    except Exception as e:
        logging.exception("Error indexing space %s: %s", space, e)

    return documents


def build_summary_index(docs: Sequence[Document], model_settings: ModelUsageSettingsCollection) -> VectorStoreIndex:
    """Build summary index."""
    service_context = _get_service_context(model_settings)
    # https://gpt-index.readthedocs.io/en/stable/core_modules/query_modules/query_engine/response_modes.html
    response_synthesizer = get_response_synthesizer(
        response_mode=ResponseMode.COMPACT, use_async=True, service_context=service_context
    )

    doc_summary_index = DocumentSummaryIndex.from_documents(
        docs,
        service_context=service_context,
        response_synthesizer=response_synthesizer,
    )
    return doc_summary_index


spaces = list_shared_spaces()
selected = st.selectbox(
    "Space",
    spaces,
    format_func=lambda x: x[2],
    label_visibility="visible",
    index=0,
)
input_prompt = st.text_input(
    label="Prompt",
)

selected_org_id = get_selected_org_id()

space = SpaceKey(SpaceType.SHARED, selected[0], selected_org_id)

saved_model_settings = get_saved_model_settings_collection(selected_org_id)

vector_index = load_index(space, saved_model_settings)

if st.button("Query Main Index"):
    # response = index_.as_query_engine(response_mode="tree_summarize", verbose=True).query(input_prompt)
    response = custom_query_engine(vector_index).query(input_prompt)
    st.write(response)

if st.button("Query Summary Index"):
    # response = index_.as_query_engine(response_mode="tree_summarize", verbose=True).query(input_prompt)
    exp_id = "summary_index_1"

    try:
        vector_index = load_index(space, saved_model_settings, exp_id)
    except Exception as e:
        raise e
        docs = get_space_document_objects(space)
        st.write(str(len(docs)))
        vector_index = build_summary_index(docs, saved_model_settings)
        vector_index.storage_context.persist(persist_dir=get_exp_index_dir(space, exp_id))

    response = vector_index.as_query_engine().query(input_prompt)
    st.write(response)

if st.button("Evaluate Index"):

    async def func() -> None:
        """Evaluate index."""
        retriever = vector_index.as_retriever()
        retriever_evaluator = RetrieverEvaluator.from_metric_names(["mrr", "hit_rate"], retriever=retriever)

        # retriever_evaluator.evaluate(query="query", expected_ids=["node_id1", "node_id2"])
        from llama_index.evaluation import generate_question_context_pairs

        qa_dataset = generate_question_context_pairs(
            [n for k, n, in vector_index.docstore.docs.items()],
            llm=_get_completion_model(saved_model_settings),
            num_questions_per_chunk=2,
        )
        eval_results = await retriever_evaluator.aevaluate_dataset(qa_dataset)
        st.write(eval_results)

    asyncio.run(func())

selected_doc = st.selectbox(
    f"Index Docs {str(len(vector_index.ref_doc_info))}",
    vector_index.ref_doc_info.keys(),
    label_visibility="visible",
    index=0,
)


st.write(vector_index.ref_doc_info.get(selected_doc))
