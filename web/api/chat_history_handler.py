"""Handle /api/chat/history requests."""
from datetime import datetime
from typing import Optional, Self

import docq.domain as domain
import docq.run_queries as rq
from pydantic import Field, ValidationError
from tornado.web import HTTPError

from web.api.models import ChatHistoryModel, MessageModel
from web.api.utils import BaseRequestHandler, CamelModel, authenticated
from web.utils.streamlit_application import st_app


class PostRequestModel(CamelModel):
    """Pydantic model for the request body."""
    pass

class PostResponseModel(CamelModel):
    """Pydantic model for the response body."""
    pass

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


def _format_chat_message(message: tuple[int, str, bool, datetime, int]) -> MessageModel:
    """Format chat message."""
    return MessageModel(
        id=message[0],
        message=message[1],
        human=message[2],
        timestamp=str(message[3]),
        thread_id=message[4],
    )

@st_app.api_route("/api/chat/history")
class ChatHistoryHandler(BaseRequestHandler):
    """Handle /api/chat/history requests."""

    @authenticated
    def get(self: Self) -> None:
        """Handle GET request."""
        limit = self.get_argument("limit", str(10))
        thread_id = self.get_argument("thread_id")
        feature_type_= self.get_argument("feature_type", domain.OrganisationFeatureType.CHAT_PRIVATE.name)


        feature_type: Optional[domain.OrganisationFeatureType] = None

        for feature in domain.OrganisationFeatureType:
            if feature.name == feature_type_:
                feature_type = feature
                break

        if feature_type is None:
            feature_type = domain.OrganisationFeatureType.CHAT_PRIVATE

        feature = domain.FeatureKey(
            type_=feature_type,
            id_=self.current_user.uid,
        )

        try:
            chat_history = rq._retrieve_messages(
                datetime.now(),
                int(limit),
                feature,
                int(thread_id),
            )
            messages = list(map(_format_chat_message, chat_history))

            self.write(ChatHistoryModel(response=messages).model_dump())

        except ValidationError as e:
            raise HTTPError(400, "Invalid page or limit") from e
