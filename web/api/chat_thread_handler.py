"""Handle /api/chat/completion requests."""
from typing import Self

import docq.run_queries as rq
from docq.domain import FeatureKey, OrganisationFeatureType
from pydantic import ValidationError
from tornado.web import HTTPError

from web.api.models import ThreadModel, ThreadPostRequestModel, ThreadResponseModel
from web.api.utils import BaseRequestHandler, authenticated
from web.utils.streamlit_application import st_app


def _get_thread_object(result: tuple) -> dict:
    return {
        'id': result[0],
        'topic': result[1],
        'created_at': str(result[2])
    }


@st_app.api_route(r"/api/chat/thread/([^/]+)?")
class ChatThreadHandler(BaseRequestHandler):
    """Handle /api/chat/thread requests."""

    @property
    def feature(self: Self) -> FeatureKey:
        """Get the feature key."""
        return FeatureKey(OrganisationFeatureType.CHAT_PRIVATE, self.current_user.uid)

    @authenticated
    def get(self: Self, id_: str) -> None:
        """Handle GET request."""
        try:
            if id_ == "latest":
                thread = rq.get_latest_thread(self.feature)
                thread_response = [ThreadModel(**_get_thread_object(thread))] if thread is not None else []

            elif id_ is None:
                threads = rq.list_thread_history(self.feature)
                thread_response = [
                    ThreadModel(**_get_thread_object(threads[i])) for i in range(len(threads))
                ] if len(threads) > 0 else []
            else:
                thread = rq.list_thread_history(self.feature, int(id_))
                thread_response = [ThreadModel(**_get_thread_object(thread[0]))] if len(thread) > 0 else []

            response = ThreadResponseModel(response=thread_response).model_dump() if len(thread_response) > 0 else {'response': []}
            self.write(response)

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Bad request", log_message=str(e)) from e

    @authenticated
    def post(self: Self, _: str) -> None:
        """Handle POST request."""
        try:
            body = ThreadPostRequestModel.model_validate_json(self.request.body)
            thread_id = rq.create_history_thread(body.topic, self.feature)
            thread = rq.list_thread_history(self.feature, thread_id)
            self.write(ThreadResponseModel(response=[ThreadModel(**_get_thread_object(thread[0]))]).model_dump())

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Invalid request body", log_message=str(e)) from e
