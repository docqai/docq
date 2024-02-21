"""GET /api/top-questions?size=x&thread_id=y."""

from typing import Any, Self

from docq.model_selection.main import get_saved_model_settings_collection
from llama_index import DocumentSummaryIndex
from tornado.web import HTTPError

from web.api.base import BaseRagRequestHandler
from web.api.utils import authenticated
from web.ml_eng_tools.visualise_index import _load_index
from web.utils.streamlit_application import st_app


@st_app.api_route(r"/api/top-questions")
class FileUploadHandler(BaseRagRequestHandler):
    """Handle GET /api/top-questions requests.

    Query Parameters:
        thread_id: int (required) - The thread id.
    """

    def get_summary_questions(self: Self) -> Any:
        """Get top possible questions from a document index."""
        model_settings = get_saved_model_settings_collection(self.selected_org_id)
        index = _load_index(self.space, model_settings)
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
