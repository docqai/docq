"""Handle /api/chat/history requests."""
from datetime import datetime
from typing import Literal, Self

import docq.run_queries as rq
from docq.domain import FeatureKey, OrganisationFeatureType
from pydantic import ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import ChatHistoryModel, MessageModel
from web.api.utils.auth_utils import authenticated
from web.utils.streamlit_application import st_app


def _format_chat_message(message: tuple[int, str, bool, datetime, int]) -> MessageModel:
    """Format chat message."""
    return MessageModel(
        id=message[0],
        message=message[1],
        human=message[2],
        timestamp=str(message[3]),
        thread_id=message[4],
    )

@st_app.api_route(r"/api/v1/([^/]+)/history/([^/]+)?")
class ChatHistoryHandler(BaseRequestHandler):
    """Handle /api/v1/<chat|rag>/thread/{thread_id}/history requests.

    /api/v1/<chat|rag>/thread/{thread_id}/history - history belongs to a thread hence resource hierarchy in the URL.
    /api/v1/<chat|rag>/thread/{thread_id}/history?page=1&page_size=10&order=desc
    """

    __feature: FeatureKey

    @property
    def feature(self: Self) -> FeatureKey:
        """Get the feature key."""
        return self.__feature

    @feature.setter
    def feature(self: Self, mode: Literal["rag", "chat"]) -> None:
        """Set the feature key."""
        if mode not in ["rag", "chat"]:
            raise HTTPError(status_code=404, reason="Not Found")

        self.__feature = FeatureKey(OrganisationFeatureType.CHAT_PRIVATE, self.current_user.uid) if mode == "chat" else FeatureKey(OrganisationFeatureType.ASK_SHARED, self.current_user.uid)

    @authenticated
    def get(self: Self, mode: Literal["rag", "chat"], thread_id: str) -> None:
        """Handle GET request."""
        self.feature = mode

        size = self.get_argument("size", "10")
        try:
            chat_history = rq._retrieve_messages(datetime.now(), int(size), self.feature, int(thread_id))
            messages = list(map(_format_chat_message, chat_history))
            self.write(ChatHistoryModel(response=messages).model_dump())

        except ValidationError as e:
            raise HTTPError(400, "Invalid page or limit") from e
