"""GET /api/top-questions?size=x&thread_id=y."""

from typing import Any, Self

from docq.domain import SpaceKey
from docq.model_selection.main import LlmUsageSettingsCollection, get_saved_model_settings_collection
from docq.support.llm import _get_service_context, _get_storage_context
from llama_index import DocumentSummaryIndex, load_index_from_storage
from llama_index.indices.base import BaseIndex
from tornado.web import HTTPError

from web.api.base_handlers import BaseRagRequestHandler
from web.api.utils.auth_utils import authenticated
from web.utils.streamlit_application import st_app


@st_app.api_route(r"/api/v1/top-questions")
class FileUploadHandler(BaseRagRequestHandler):
    """Handle GET /api/v1/top-questions requests.

    Query Parameters:
        thread_id: int (required) - The thread id.
    """

    def _load_index(self: Self, space: SpaceKey, model_settings_collection: LlmUsageSettingsCollection) -> BaseIndex:
        """Load index from storage."""
        storage_context = _get_storage_context(space)
        service_context = _get_service_context(model_settings_collection)
        return load_index_from_storage(storage_context=storage_context, service_context=service_context)

    def get_summary_questions(self: Self) -> Any:
        """Get top possible questions from a document index."""
        model_settings = get_saved_model_settings_collection(self.selected_org_id)
        index = self._load_index(self.space, model_settings)
        if not isinstance(index, DocumentSummaryIndex):
            raise HTTPError(404, reason="DocumentSummaryIndex not found")

        docs = index.docstore.docs
        summary_questions = []
        for _, summary_node_id in index.index_struct.doc_id_to_summary_id.items():
            summary_node = docs[summary_node_id]

            text_summary: str = summary_node.to_dict().get("text", None)
            if text_summary:
                summary_questions += text_summary.split("\n- ")[1:]
        return {"questions": summary_questions}


    @authenticated
    def get(self: Self) -> None:
        """Handle GET top questions request."""
        try:
            self.write(self.get_summary_questions())
        except Exception as e:
            raise HTTPError(500, reason="Internal server error") from e
