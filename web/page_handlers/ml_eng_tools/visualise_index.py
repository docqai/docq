"""ML Eng - Visualise index."""

from typing import Optional, cast

import streamlit as st
from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_spaces import list_space
from docq.model_selection.main import LlmUsageSettingsCollection, get_saved_model_settings_collection
from docq.support.llm import _get_service_context
from docq.support.store import _get_storage_context
from llama_index.core.indices import DocumentSummaryIndex, VectorStoreIndex, load_index_from_storage
from llama_index.core.indices.base import BaseIndex
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface_optimum import OptimumEmbedding
from utils.layout import auth_required, render_page_title_and_favicon
from utils.sessions import get_selected_org_id

from ..ml_eng_tools.visualise_vector_store_index import visualise_vector_store_index

render_page_title_and_favicon()
auth_required(requiring_selected_org_admin=True)


test1 = st.button("Embedding Test")

if test1:
    OptimumEmbedding.create_and_save_optimum_model("BAAI/bge-small-en-v1.5", "./.persisted/models/bge_onnx")
    # embed_model = OptimumEmbedding(folder_name=get_models_dir("BAAI/bge-small-en-v1.5"))
    embed_model = OptimumEmbedding(folder_name="./.persisted/models/bge_onnx")
    # _tokenizer = AutoTokenizer.from_pretrained("./.persisted/models/bge_onnx")
    # sentences = ["Hello World!"]
    # encoded_input = _tokenizer(
    #     sentences,
    #     padding=True,
    #     max_length=512,
    #     truncation=True,
    #     return_tensors="pt",
    # )
    # print(encoded_input)
    # encoded_input.pop("token_type_ids", None)
    # print(encoded_input)
    # embed_model = OptimumEmbedding(folder_name="./.persisted/models/bge_onnx", tokenizer=_tokenizer)

    # Settings.embed_model = embed_model
    embeddings = embed_model.get_text_embedding("Hello World!")
    print("embedding len: ", len(embeddings))
    print("embedding", embeddings[:5])


def _load_index(
    space: SpaceKey, model_settings_collection: LlmUsageSettingsCollection, exp_id: Optional[str] = None
) -> BaseIndex:
    """Load index from storage."""
    storage_context = _get_storage_context(space)
    service_context = _get_service_context(model_settings_collection)
    return load_index_from_storage(storage_context=storage_context, service_context=service_context)


selected_org_id = get_selected_org_id()
spaces = []
selected_space = None
if selected_org_id:
    spaces.extend(list_space(selected_org_id, SpaceType.SHARED.name))
    spaces.extend(list_space(selected_org_id, SpaceType.THREAD.name))
    #list_shared_spaces(org_id=selected_org_id)
    selected_space = st.selectbox(
        "Space",
        spaces,
        format_func=lambda x: x[2],
        label_visibility="visible",
        index=0,
    )


def visualise_document_summary_index(_index: DocumentSummaryIndex) -> None:
    """Visualise document summary index."""
    docs = _index.docstore.docs
    st.write(f"Index class: `{_index.index_struct_cls.__name__}`")
    st.write("Total Docs: ", len(_index.index_struct.doc_id_to_summary_id.items()), " | ", "Total Chunks: ", len(docs))

    for doc_id, summary_node_id in _index.index_struct.doc_id_to_summary_id.items():
        summary_node = docs[summary_node_id]

        node_ids = _index.index_struct.summary_id_to_node_ids[summary_node_id]
        st.write(f"**Document ID**: `{doc_id}`, **Chunks**: `{len(node_ids)}`")




        with st.expander(label=f"**Summary** NodeID: `{summary_node_id}`"):
            st.write(summary_node.to_dict())

        for node_id in node_ids:
            with st.expander(label=f"**Chunk** NodeID: `{node_id}`"):
                node: TextNode = cast(TextNode, docs[node_id])
                st.write(node.to_dict())

            metadata = docs[node_id].to_dict()["metadata"]
            if "excerpt_keywords" in metadata:
                keyword_count = len(docs[node_id].to_dict()["metadata"]["excerpt_keywords"].split(", "))
                st.write(f"Metadata Keyword Count: {keyword_count}")
            # for key, entity_label in DEFAULT_ENTITY_MAP.items():
            #     if entity_label in metadata:
            #         x_count = len(metadata[entity_label])
            #         st.write(f"Metadata Entity '{entity_label}' count: {x_count}")

        st.divider()


if selected_space and selected_org_id:
    print("selected_space type: ", selected_space[7])

    space = SpaceKey(SpaceType[selected_space[7]], selected_space[0], selected_org_id)

    saved_model_settings = get_saved_model_settings_collection(selected_org_id)


    _index = _load_index(space, saved_model_settings)
    if isinstance(_index, DocumentSummaryIndex):
        visualise_document_summary_index(_index)
    elif isinstance(_index, VectorStoreIndex):
        visualise_vector_store_index(_index)
    else:
        st.write("Visualiser not available for index type: ", _index.index_struct_cls.__name__)
