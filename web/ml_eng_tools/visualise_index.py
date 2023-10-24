import json
from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_spaces import list_shared_spaces
from docq.model_selection.main import ModelUsageSettingsCollection, get_saved_model_settings_collection
from docq.support.llm import _get_service_context, _get_storage_context
from llama_index import VectorStoreIndex, load_index_from_storage
from st_pages import _add_page_title
import streamlit as st
from utils.layout import auth_required
from utils.sessions import get_selected_org_id
from llama_index.schema import MetadataMode


auth_required(requiring_admin=True)

_add_page_title()


def _load_index(
    space: SpaceKey, model_settings_collection: ModelUsageSettingsCollection, exp_id: str = None
) -> VectorStoreIndex:
    """Load index from storage."""
    storage_context = _get_storage_context(space)
    service_context = _get_service_context(model_settings_collection)
    return load_index_from_storage(storage_context=storage_context, service_context=service_context)


selected_org_id = get_selected_org_id()
spaces = list_shared_spaces(org_id=selected_org_id)
selected_space = st.selectbox(
    "Space",
    spaces,
    format_func=lambda x: x[2],
    label_visibility="visible",
    index=0,
)


space = SpaceKey(SpaceType.SHARED, selected_space[0], selected_org_id)

saved_model_settings = get_saved_model_settings_collection(selected_org_id)


vector_index = _load_index(space, saved_model_settings)
docs = vector_index.docstore.docs


for doc_id in docs:
    with st.expander(label=doc_id):
        doc_json = json.loads(docs[doc_id].to_json())
        # st.write(docs[doc_id].get_content(metadata_mode=MetadataMode.ALL))
        st.write(doc_json)
