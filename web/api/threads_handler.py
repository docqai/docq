"""Handle chat and rag threads."""
from datetime import datetime
from typing import Literal, Self

import docq.run_queries as rq
from docq.domain import SpaceKey
from docq.model_selection.main import LlmUsageSettingsCollection, get_saved_model_settings_collection
from docq.support.llm import _get_service_context, _get_storage_context
from llama_index import DocumentSummaryIndex, load_index_from_storage
from llama_index.indices.base import BaseIndex
from pydantic import ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRagRequestHandler, BaseRequestHandler
from web.api.models import ChatHistoryModel, ThreadModel, ThreadPostRequestModel, ThreadResponseModel
from web.api.utils.auth_utils import authenticated
from web.utils.streamlit_application import st_app


def _get_thread_object(result: tuple) -> dict:
    return {"id": result[0], "topic": result[1], "created_at": str(result[2])}


@st_app.api_route("/api/v1/{feature}/threads")
class ThreadsHandler(BaseRequestHandler):
    """Handle /api/v1/{feature}/thread requests.

    Path Parameters:
        feature (Literal["rag", "chat"]): The feature type, used to select between general chat and shared ask.
    """

    @authenticated
    def get(self: Self, feature: Literal["rag", "chat"]) -> None:
        """Handle GET request.

        Query Parameters:
            page: int - The page number.
            page_size: int - The number of items per page.
            order: Literal["asc", "desc"] - The order of the items.

        Response:
            ThreadResponseModel - Response object model.
        """
        self.feature = feature

        try:
            threads = rq.list_thread_history(self.feature)
            thread_response = (
                [ThreadModel(**_get_thread_object(threads[i])) for i in range(len(threads))] if len(threads) > 0 else []
            )
            response = (
                ThreadResponseModel(response=thread_response).model_dump()
                if len(thread_response) > 0
                else {"response": []}
            )
            self.write(response)

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Bad request", log_message=str(e)) from e

    @authenticated
    def post(self: Self, feature: Literal["rag", "chat"]) -> None:
        """Handle POST request.

        Request Body:
            topic: str - Thread topic, A brief description of what the thread is about.

        Response:
            ThreadResponseModel - Response object model.
        """
        self.feature = feature

        try:
            request = ThreadPostRequestModel.model_validate_json(self.request.body)
            thread_id = rq.create_history_thread(request.topic, self.feature)
            thread = rq.list_thread_history(self.feature, thread_id)
            self.write(ThreadResponseModel(response=[ThreadModel(**_get_thread_object(thread[0]))]).model_dump())

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Invalid request body", log_message=str(e)) from e


@st_app.api_route("/api/v1/{feature}/threads/{thread_id: int}")
class ThreadHandler(BaseRequestHandler):
    """Handle /api/v1/{thread_type}threads/{thread_id} requests.

    Path Parameters:
        feature (Literal["rag", "chat"]): The feature type, used to select between general chat and shared ask.
        thread_id (str): The thread id or "latest".
    """

    @authenticated
    def get(self: Self, feature: Literal["rag", "chat"], thread_id: int) -> None:
        """Handle GET request."""
        self.feature = feature

        try:
            thread = rq.list_thread_history(self.feature, thread_id)
            thread_response = [ThreadModel(**_get_thread_object(thread[0]))] if len(thread) > 0 else []

            response = (
                ThreadResponseModel(response=thread_response).model_dump()
                if len(thread_response) > 0
                else {"response": []}
            )
            self.write(response)

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Bad request", log_message=str(e)) from e

    @authenticated
    def delete(self: Self, feature: Literal["rag", "chat"], thread_id: str) -> None:
        """Handle POST request."""
        self.feature = feature

        raise HTTPError(status_code=501, reason="Not implemented")

    @authenticated
    def update(self: Self, feature: Literal["rag", "chat"], thread_id: str) -> None:
        """Handle POST request."""
        self.feature = feature

        raise HTTPError(status_code=501, reason="Not implemented")


@st_app.api_route("/api/v1/{feature}/threads/{thread_id: int}/history")
class ThreadHistoryHandler(BaseRequestHandler):
    """Handle /api/v1/{thread_type}threads/{thread_id}/history requests.

    Path Parameters:
        feature (Literal["rag", "chat"]): The feature type, used to select between general chat and shared ask.
        thread_id (str): The thread id.
    """

    @authenticated
    def get(self: Self, feature: Literal["rag", "chat"], thread_id: str) -> None:
        """Handle GET request."""
        self.feature = feature
        page = self.get_argument("page", "1")  # noqa: F841
        page_size = self.get_argument("page_size", "10")
        order = self.get_argument("order", "desc")

        try:
            chat_history = rq._retrieve_messages(
                datetime.now(), int(page_size), self.feature, int(thread_id), "ASC" if order == "asc" else "DESC"
            )
            messages = list(map(self._get_message_object, chat_history))
            self.write(ChatHistoryModel(response=messages).model_dump())
        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Invalid page or limit") from e


@st_app.api_route("/api/v1/rag/threads/{thread_id: int}/top-questions")
class TopQuestionsHandler(BaseRagRequestHandler):
    """Handle GET /api/v1/rag/threads/id/top-questions request."""

    def _load_index(self: Self, space: SpaceKey, model_settings_collection: LlmUsageSettingsCollection) -> BaseIndex:
        """Load index from storage."""
        storage_context = _get_storage_context(space)
        service_context = _get_service_context(model_settings_collection)
        return load_index_from_storage(storage_context=storage_context, service_context=service_context)

    def get_summary_questions(self: Self) -> dict:
        """Get top possible questions from a document index."""
        model_settings = get_saved_model_settings_collection(self.selected_org_id)
        index = self._load_index(self.thread_space, model_settings)
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
    def get(self: Self, thread_id: int) -> None:
        """Handle GET top questions request."""
        self.feature = "rag"
        self.thread_space = thread_id
        try:
            self.write(self.get_summary_questions())
        except Exception as e:
            raise HTTPError(500, reason="Internal server error") from e
