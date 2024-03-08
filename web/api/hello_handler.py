"""Handle /api/hello requests."""
from typing import Self

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
