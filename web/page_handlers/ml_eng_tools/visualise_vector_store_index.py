import json

import streamlit as st
from llama_index.core.indices import VectorStoreIndex


def visualise_vector_store_index(_index: VectorStoreIndex) -> None:
    """Visualise document summary index."""
    docs = _index.docstore.docs
    st.write("Index class: ", _index.index_struct_cls.__name__)
    for doc_id in docs:
        doc_json = json.loads(docs[doc_id].to_json())
        # st.write(docs[doc_id].get_content(metadata_mode=MetadataMode.ALL))
        metadata_keys = doc_json["metadata"].keys()

        with st.expander(label=doc_id):
            st.write(doc_json)

        if "excerpt_keywords" in metadata_keys:
            keyword_count = len(doc_json["metadata"]["excerpt_keywords"].split(", "))
            st.write(f"Metadata Keyword Count: {keyword_count}")

        # for key, entity_label in DEFAULT_ENTITY_MAP.items():
        #     if entity_label in metadata_keys:
        #         x_count = len(doc_json["metadata"][entity_label])
        #         st.write(f"Metadata Entity '{entity_label}' count: {x_count}")
