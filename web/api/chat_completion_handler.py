"""Handle /api/chat/completion requests."""
import random
from typing import Optional, Self

import docq.run_queries as rq
from docq.domain import FeatureKey, OrganisationFeatureType
from docq.manage_personas import get_persona
from docq.model_selection.main import get_model_settings_collection
from pydantic import Field, ValidationError
from tornado.web import HTTPError

from web.api.base import BaseRequestHandler
from web.api.models import MessageModel, MessageResponseModel
from web.api.utils import CamelModel, authenticated
from web.utils.streamlit_application import st_app


class PostRequestModel(CamelModel):
    """Pydantic model for the request body."""
    input_: str = Field(..., alias="input")
    thread_id: Optional[int] = Field(None)
    history: Optional[str] = Field(None)
    llm_settings_collection_name: Optional[str] = Field(None)
    persona_key: Optional[str] = Field(None)


@st_app.api_route("/api/chat/completion")
class ChatCompletionHandler(BaseRequestHandler):
    """Handle /api/chat/completion requests."""

    @property
    def feature(self: Self) -> FeatureKey:
        """Get the feature key."""
        return FeatureKey(OrganisationFeatureType.CHAT_PRIVATE, self.current_user.uid)

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
            model_usage_settings = get_model_settings_collection(request_model.llm_settings_collection_name) if request_model.llm_settings_collection_name else get_model_settings_collection("azure_openai_latest")
            persona = get_persona(request_model.persona_key if request_model.persona_key else "default")
            thread_id = request_model.thread_id

            if thread_id is None:
                thread_id = rq.create_history_thread(
                    f"{request_model.input_[:100]}-{random.randint(1, 100000)}",  # noqa: S311
                    self.feature
                )

            result = rq.query(input_=request_model.input_, feature=self.feature, thread_id=thread_id, model_settings_collection=model_usage_settings, persona=persona )

            messages = [
                MessageModel(**self._get_message_object(result[i])) for i in range(2)
            ]

            response_model = MessageResponseModel(response=messages, meta={"model_settings": model_usage_settings.key})

            self.write(response_model.model_dump())

        except ValidationError as e:
            raise HTTPError(status_code=400, reason="Invalid request body", log_message=str(e)) from e

