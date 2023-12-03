"""Handle /api/chat/completion requests."""
import json
from typing import Self

from docq.model_selection.main import get_model_settings_collection
from docq.run_queries import run_chat
from tornado.web import RequestHandler

from web.utils.streamlit_application import st_app

from .utils import authenticated


@st_app.api_route("/api/chat/completion")
class ChatCompletionHandler(RequestHandler):
    """Handle /api/chat/completion requests."""

    def check_origin(self: Self, origin) -> bool:
        """Override the origin check if it's causing problems."""
        return True

    def check_xsrf_cookie(self) -> bool:
        # If `True`, POST, PUT, and DELETE are block unless the `_xsrf` cookie is set.
        # Safe with token based authN
        return False

    def get(self: Self) -> None:
        """Handle GET request."""
        self.write({"message": "hello world 2"})

    @authenticated
    def post(self: Self) -> None:
        """Handle POST request.

        Example:
        ```shell
        curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer expected_token" -d /
        '{"input":"whats the sun?"}' http://localhost:8501/api/chat/completion
        ```
        """
        body = self.request.body
        # Parse the request body as JSON
        payload = json.loads(body)
        # Extract parameters from the JSON
        input_ = payload.get("input")
        model_usage_settings = get_model_settings_collection("azure_openai_latest")
        result = run_chat(input_=input_, history="", model_settings_collection=model_usage_settings)
        self.write(result.response)
