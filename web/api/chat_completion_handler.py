"""Handle /api/chat/completion requests."""
from typing import Optional, Self

import docq.run_queries as rq
from docq.manage_personas import get_persona
from docq.model_selection.main import get_model_settings_collection
from pydantic import Field, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import MessageResponseModel
from web.api.utils.auth_utils import authenticated
from web.api.utils.docq_utils import get_feature_key, get_message_object
from web.api.utils.pydantic_utils import CamelModel
from web.utils.streamlit_application import st_app


class PostRequestModel(CamelModel):
    """Pydantic model for the request body."""

    input_: str = Field(..., alias="input")
    thread_id: int
    history: Optional[str] = Field(None)
    llm_settings_collection_name: Optional[str] = Field(None)
    persona_key: Optional[str] = Field(None)


@st_app.api_route("/api/v1/chat/completion")
class ChatCompletionHandler(BaseRequestHandler):
    """Handle /api/chat/completion requests."""

    @authenticated
    def post(self: Self) -> None:
        """Handle POST request.

        Example:
        ```sh
        curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer expected_token" -d /
        '{"input":"what is the sun?", "modelSettingsCollectionName"}' http://localhost:8501/api/v1/chat/completion
        ```
        """
        feature = get_feature_key(self.current_user.uid, "chat")
        try:
            request = PostRequestModel.model_validate_json(self.request.body)
            model_usage_settings = (
                get_model_settings_collection(request.llm_settings_collection_name)
                if request.llm_settings_collection_name
                else get_model_settings_collection("azure_openai_latest")
            )
            persona = get_persona(request.persona_key if request.persona_key else "default")
            thread_id = request.thread_id

            result = rq.query(
                input_=request.input_,
                feature=feature,
                thread_id=thread_id,
                model_settings_collection=model_usage_settings,
                persona=persona,
            )
            messages = list(map(get_message_object, result))
            response_model = MessageResponseModel(response=messages, meta={"model_settings": model_usage_settings.key})

            self.write(response_model.model_dump())

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Invalid request body", log_message=str(e)) from e
