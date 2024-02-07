"""Handle /api/chat/history requests."""
from datetime import datetime
from typing import Any, Optional, Self

import docq.domain as domain
import docq.run_queries as rq
from pydantic import Field, ValidationError
from tornado.web import HTTPError, RequestHandler

from web.api.utils import CamelModel, authenticated
from web.utils.streamlit_application import st_app


class PostRequestModel(CamelModel):
    """Pydantic model for the request body."""
    pass

class PostResponseModel(CamelModel):
    """Pydantic model for the response body."""
    pass

class ChatHistoryModel(CamelModel):
    """Pydantic model for the chat history object."""
    id_: int = Field(..., alias="id")
    message: str
    human: bool
    timestamp: datetime
    thread_id: int

class ApiInfoModel(CamelModel):
    """Pydantic model for the API info."""
    page: int = 1
    limit: int = 10
    count: int
    next_: Optional[str] = Field(None, alias="next")
    prev: Optional[str] = Field(None)

class GetResponseModel(CamelModel):
    """Pydantic model for the request body."""
    messages: list[ChatHistoryModel]
    info: ApiInfoModel


def _format_chat_message(message: tuple[int, str, bool, datetime, int]) -> ChatHistoryModel:
    """Format chat message."""
    return ChatHistoryModel(
        id=message[0],
        message=message[1],
        human=message[2],
        timestamp=message[3],
        thread_id=message[4],
    )

@st_app.api_route("/api/chat/history")
class ChatHistoryHandler(RequestHandler):
    """Handle /api/chat/history requests."""

    def check_origin(self: Self, origin: Any) -> bool:
        """Override the origin check if it's causing problems."""
        return True

    def check_xsrf_cookie(self: Self) -> bool:
        """Override the XSRF cookie check."""
        # If `True`, POST, PUT, and DELETE are block unless the `_xsrf` cookie is set.
        # Safe with token based authN
        return False

    @authenticated
    def get(self: Self) -> None:
        """Handle GET request."""
        page = self.get_argument("page", str(1))
        limit = self.get_argument("limit", str(10))
        thread_id = self.get_argument("thread_id")
        user_id = self.get_argument("user_id")
        feature_type_= self.get_argument("feature_type", domain.OrganisationFeatureType.CHAT_PRIVATE.name)

        if not (bool(thread_id) and bool(user_id)):
            raise HTTPError(400, "thread_id and feature_key are required")

        feature_type: Optional[domain.OrganisationFeatureType] = None

        for feature in domain.OrganisationFeatureType:
            if feature.name == feature_type_:
                feature_type = feature
                break

        if feature_type is None:
            feature_type = domain.OrganisationFeatureType.CHAT_PRIVATE

        feature = domain.FeatureKey(
            type_=feature_type,
            id_=int(user_id)
        )

        try:
            chat_history = rq._retrieve_messages(
                datetime.now(),
                int(limit),
                feature,
                int(thread_id),
            )
            messages = list(map(_format_chat_message, chat_history))
            info = ApiInfoModel(
                page=int(page),
                limit=int(limit),
                count=len(messages),
                prev=None,
                next=None,
            )
            self.write(GetResponseModel(messages=messages, info=info).model_dump())

        except ValidationError as e:
            raise HTTPError(400, "Invalid page or limit") from e
