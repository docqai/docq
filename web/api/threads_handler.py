"""Handle chat and rag threads."""
from datetime import datetime
from typing import Self

import docq.manage_spaces as ms
import docq.run_queries as rq
from docq.data_source.list import SpaceDataSources
from docq.domain import SpaceKey
from docq.model_selection.main import LlmUsageSettingsCollection, get_saved_model_settings_collection
from docq.support.llm import _get_service_context
from docq.support.store import _get_storage_context
from llama_index.core.indices import DocumentSummaryIndex, load_index_from_storage
from llama_index.core.indices.base import BaseIndex
from pydantic import ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import (
    FEATURE,
    ThreadHistoryModel,
    ThreadHistoryResponseModel,
    ThreadModel,
    ThreadPostRequestModel,
    ThreadResponseModel,
    ThreadsResponseModel,
)
from web.api.utils.auth_utils import authenticated
from web.api.utils.docq_utils import get_feature_key, get_message_object, get_thread_space
from web.utils.streamlit_application import st_app


def _get_thread_object(result: tuple) -> dict:
    # TODO: when we refactor the data layer to return data model classes instead of tuples, we can remove this function
    return {"id": result[0], "topic": result[1], "created_at": str(result[2])}


@st_app.api_route("/api/v1/{feature}/threads")
class ThreadsHandler(BaseRequestHandler):
    """Handle /api/v1/{feature}/thread requests.

    Path Parameters:
        feature (Literal["rag", "chat"]): The feature type, used to select between general chat and shared ask.
    """

    @authenticated
    def get(self: Self, feature_: FEATURE) -> None:
        """Handle GET request.

        Query Parameters:
            page: int - The page number.
            page_size: int - The number of items per page.
            order: Literal["asc", "desc"] - The order of the items.

        Response:
            ThreadsResponseModel - Response object model.
        """
        feature = get_feature_key(self.current_user.uid, feature_)

        try:
            threads = rq.list_thread_history(feature)
            thread_response = (
                [ThreadModel(**_get_thread_object(threads[i])) for i in range(len(threads))] if len(threads) > 0 else []
            )
            response = (
                ThreadsResponseModel(response=thread_response).model_dump(by_alias=True)
                if len(thread_response) > 0
                else {"response": []}
            )
            self.write(response)

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Bad request", log_message=str(e)) from e

    @authenticated
    def post(self: Self, feature_: FEATURE) -> None:
        """POST: Handle creating a new Thread.

        Request Body:
            topic: str - Thread topic, A brief description of what the thread is about.

        Response:
            ThreadResponseModel - Response object model.
        """
        feature = get_feature_key(self.current_user.uid, feature_)

        try:
            request = ThreadPostRequestModel.model_validate_json(self.request.body)
            thread_id = rq.create_history_thread(request.topic, feature)
            thread = rq.list_thread_history(feature, thread_id)
            if not thread_id:
                raise HTTPError(status_code=500, reason="Internal server error", log_message="Thread creation failed.")

            space_thread = ms.create_thread_space(
                self.selected_org_id, thread_id, request.topic, SpaceDataSources.MANUAL_UPLOAD.name
            )
            print("space_thread: ", space_thread)
            self.set_status(201)  # 201 Created
            self.write(
                ThreadResponseModel(response=ThreadModel(**_get_thread_object(thread[0]))).model_dump(by_alias=True)
            )

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Invalid request body", log_message=str(e)) from e


@st_app.api_route("/api/v1/{feature}/threads/{thread_id}")
class ThreadHandler(BaseRequestHandler):
    """Handle /api/v1/{thread_type}threads/{thread_id} requests.

    Path Parameters:
        feature (Literal["rag", "chat"]): The feature type, used to select between general chat and shared ask.
        thread_id (str): The thread id or "latest".
    """

    @authenticated
    def get(self: Self, feature_: FEATURE, thread_id: int) -> None:
        """Handle GET request."""
        feature = get_feature_key(self.current_user.uid, feature_)

        try:
            thread = rq.list_thread_history(feature, thread_id)
            thread_response = ThreadModel(**_get_thread_object(thread[0])) if len(thread) > 0 else None

            if not thread_response:
                raise HTTPError(404, reason="Thread not found.")

            response = ThreadResponseModel(response=thread_response).model_dump(by_alias=True)
            self.write(response)

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Bad request", log_message=str(e)) from e
        except HTTPError as e:
            raise e
        except Exception as e:
            raise HTTPError(status_code=500, reason="Internal server error", log_message=str(e)) from e

    @authenticated
    def delete(self: Self, feature_: FEATURE, thread_id: str) -> None:
        """Handle DELETE request."""
        feature = get_feature_key(self.current_user.uid, feature_)
        thread_exists = rq.thread_exists(int(thread_id), self.current_user.uid, feature.type_)
        is_deleted = False
        if thread_exists:
            is_deleted = rq.delete_thread(int(thread_id), feature)

        if is_deleted:
            self.set_status(204)  # 204 No Content
        elif not thread_exists:
            raise HTTPError(status_code=404, reason="Thread not found.")
        else:
            raise HTTPError(status_code=500, reason="Internal server error")

    @authenticated
    def update(self: Self, feature_: FEATURE, thread_id: str) -> None:
        """Handle POST request."""
        raise HTTPError(status_code=501, reason="Update thread - Not implemented")


@st_app.api_route("/api/v1/{feature}/threads/{thread_id}/history")
class ThreadHistoryHandler(BaseRequestHandler):
    """Handle /api/v1/{thread_type}threads/{thread_id}/history requests.

    Path Parameters:
        feature (Literal["rag", "chat"]): The feature type, used to select between general chat and shared ask.
        thread_id (str): The thread id.
    """

    @authenticated
    def get(self: Self, feature_: FEATURE, thread_id: str) -> None:
        """GET: history messages for a thread."""
        feature = get_feature_key(self.current_user.uid, feature_)
        page = self.get_argument("page", "1")  # noqa: F841
        page_size = self.get_argument("page_size", "10")
        order = self.get_argument("order", "desc")

        try:
            thread = rq.list_thread_history(feature, int(thread_id))

            if not len(thread) > 0:
                raise HTTPError(status_code=404, reason="Thread not found")

            thread_history = rq._retrieve_messages(
                datetime.now(), int(page_size), feature, int(thread_id), "ASC" if order == "asc" else "DESC"
            )

            messages = list(map(get_message_object, thread_history))
            thread_history_model = ThreadHistoryModel(**_get_thread_object(thread[0]), messages=messages)

            thread_history_response = ThreadHistoryResponseModel(response=thread_history_model)

            self.write(thread_history_response.model_dump(by_alias=True))
        except ValidationError as e:
            print("ValidationError: ", e)
            raise HTTPError(status_code=400, reason="Invalid page or limit") from e
        except HTTPError as e:
            raise e
        except Exception as e:
            raise HTTPError(status_code=500, reason="Internal server error") from e


@st_app.api_route("/api/v1/rag/threads/{thread_id}/top-questions")
class TopQuestionsHandler(BaseRequestHandler):
    """Handle GET /api/v1/rag/threads/id/top-questions request."""

    def _load_index(self: Self, space: SpaceKey, model_settings_collection: LlmUsageSettingsCollection) -> BaseIndex:
        """Load index from storage."""
        storage_context = _get_storage_context(space)  # FIXME: _get_storage_context should not be called directly here.
        service_context = _get_service_context(
            model_settings_collection
        )  # FIXME: _get_service_context should not be called directly here.
        return load_index_from_storage(storage_context=storage_context, service_context=service_context)

    def get_summary_questions(self: Self, thread_space: SpaceKey) -> dict:
        """Get top possible questions from a document index."""
        model_settings = get_saved_model_settings_collection(self.selected_org_id)
        index = self._load_index(thread_space, model_settings)
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
        thread_space = get_thread_space(self.selected_org_id, thread_id)
        try:
            self.write(self.get_summary_questions(thread_space))
        except Exception as e:
            raise HTTPError(500, reason="Internal server error") from e
