"""Handle /api/hello requests."""
import logging as log
from typing import Self

import tornado.websocket
from tornado.web import RequestHandler

from web.api.utils.pydantic_utils import CamelModel
from web.utils.streamlit_application import st_app


class ResponseModel(CamelModel):
    """Pydantic model for the response body."""
    response: str

@st_app.api_route("/api/v1/hello")
class ChatCompletionHandler(RequestHandler):
    """Handle /api/v1/hello requests."""

    def check_origin(self: Self, origin) -> bool:
        """Override the origin check if it's causing problems."""
        return True

    def check_xsrf_cookie(self) -> bool:
        # If `True`, POST, PUT, and DELETE are block unless the `_xsrf` cookie is set.
        # Safe with token based authN
        return False

    def get(self: Self) -> None:
        """Handle GET request."""
        response = ResponseModel(response="Hello World!")
        self.write(response.model_dump())


@st_app.api_route("/api/echo")
class EchoWebSocket(tornado.websocket.WebSocketHandler):
    """Handle websocket connections."""

    def check_origin(self: Self, origin: str) -> bool:
        """Override the origin check if it's causing problems."""
        return True

    def open(self: Self) -> None:  # noqa: A003
        """Handle open connection."""
        log.info("WebSocket opened")

    def on_message(self: Self, message: str) -> None:
        """Handle incoming message."""
        self.write_message(u"You said: " + message)

    def on_close(self: Self) -> None:
        """Handle closed connection."""
        log.info("WebSocket closed")
