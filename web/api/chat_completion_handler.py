"""Handle /api/chat/completion requests."""
from typing import Optional, Self

from docq.model_selection.main import get_model_settings_collection
from docq.run_queries import run_chat
from pydantic import Field, ValidationError
from tornado.web import HTTPError, RequestHandler

from web.api.utils import CamelModel, authenticated
from web.utils.streamlit_application import st_app


class PostRequestModel(CamelModel):
    """Pydantic model for the request body."""
    input_: str = Field(..., alias="input")
    history: Optional[str] = Field(None)
    model_settings_collection_name: Optional[str] = Field(None)

class PostResponseModel(CamelModel):
    """Pydantic model for the response body."""
    response: str
    meta: Optional[dict[str,str]] = None

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
        '{"input":"what's the sun?", "modelSettingsCollectionName"}' http://localhost:8501/api/chat/completion
        ```
        """
        body = self.request.body

        try:
            request_model = PostRequestModel.model_validate_json(body)
            history = request_model.history if request_model.history else ""
            model_usage_settings = get_model_settings_collection(request_model.model_settings_collection_name) if request_model.model_settings_collection_name else get_model_settings_collection("azure_openai_latest")
            result = run_chat(input_=request_model.input_, history=history, model_settings_collection=model_usage_settings)
            response_model = PostResponseModel(response=result.response, meta={"model_settings": model_usage_settings.key})

            self.write(response_model.model_dump())

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Invalid request body", log_message=str(e)) from e

