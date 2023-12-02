import json
from typing import Self

from docq.model_selection.main import get_model_settings_collection
from docq.run_queries import run_chat
from tornado.web import RequestHandler

from web.utils.streamlit_application import st_app


@st_app.api_route("/api/chat/completion")
class ChatCompletionHandler(RequestHandler):
    """Handle /api/hello2 requests."""

    def check_origin(self: Self, origin) -> bool:
        """Override the origin check if it's causing problems."""
        return True

    def get(self: Self) -> None:
        """Handle GET request."""
        self.write({"message": "hello world 2"})

    def post(self: Self) -> None:
        """Handle POST request."""
        body = self.request.body
        # Parse the request body as JSON
        payload = json.loads(body)
        # Extract parameters from the JSON
        input_ = payload.get("input")
        model_usage_settings = get_model_settings_collection("azure_openai_latest")
        result = run_chat(input_=input_, history="", model_settings_collection=model_usage_settings)
        self.write(result.response)
