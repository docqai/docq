"""Handle /api/chat/completion requests."""
from typing import Optional, Self

import docq.run_queries as rq
from docq.config import OrganisationFeatureType
from docq.domain import FeatureKey
from docq.manage_assistants import get_assistant_fixed
from docq.model_selection.main import get_model_settings_collection
from opentelemetry import trace
from pydantic import Field, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import MessagesResponseModel
from web.api.utils.auth_utils import authenticated
from web.api.utils.docq_utils import get_message_object
from web.api.utils.pydantic_utils import CamelModel
from web.utils.streamlit_application import st_app

tracer = trace.get_tracer(__name__)

class ChatCompletionPostRequestModel(CamelModel):
    """Data class for ChatCompletion POST request payload."""

    input_: str = Field(..., alias="input")
    thread_id: int = Field(..., description="id for a chat thread that belongs to the authenticated user.")
    history: Optional[str] = Field(
        None, description="chat history"
    )  # TODO: this needs to have structure not just a string.
    llm_settings_collection_name: Optional[str] = Field(None)
    assistant_key: Optional[str] = Field(None)


@st_app.api_route("/api/v1/chat/completion")
class ChatCompletionHandler(BaseRequestHandler):
    """Handle /api/chat/completion requests.

    Straight through LLM chat with threads and history.
    Requires a user context.
    """

    @authenticated
    @tracer.start_as_current_span(name="PostChatCompletionHandler")
    def post(self: Self) -> None:
        """Handle POST request.

        Example:
        ```sh
        curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer expected_token" -d /
        '{"input":"what is the sun?", "llmSettingsCollectionName": "option modelsettngs name"}' http://localhost:8501/api/v1/chat/completion
        ```
        """
        # with tracer.start_as_current_span("PostChatCompletionHandler") as span:
        span = trace.get_current_span()
        if self.current_user is None:
            span.set_status(trace.StatusCode.ERROR, "Bad request.")
            span.record_exception(
                ValueError("This endpoint requires a authenticated user context. API Key is not supported.")
            )
            raise HTTPError(
                400,
                log_message="This endpoint requires a authenticated user context. API Key is not supported.",
            )

        current_user_id = self.current_user.uid
        feature = FeatureKey(OrganisationFeatureType.CHAT_PRIVATE, current_user_id)
        try:
            try:
                payload = ChatCompletionPostRequestModel.model_validate_json(self.request.body)
            except ValidationError as e:
                span.set_status(trace.StatusCode.ERROR, "Bad request. Payload model validation error.")
                span.record_exception(e)
                raise HTTPError(status_code=400, log_message=str(e)) from e

            llm_settings_collection_name = payload.llm_settings_collection_name or "azure_openai_latest"
            model_usage_settings = get_model_settings_collection(llm_settings_collection_name)
            assistant_key = payload.assistant_key if payload.assistant_key else "default"
            assistant = get_assistant_fixed(model_usage_settings.key)[assistant_key]

            if not assistant:
                span.set_status(trace.StatusCode.ERROR, "Bad request.")
                span.record_exception(ValueError(f"Assistant key '{assistant_key}' not found."))
                raise HTTPError(status_code=400, log_message=f"Assistant key '{assistant_key}' not found.")

            thread_id = payload.thread_id

            if not rq.thread_exists(thread_id, current_user_id, feature.type_):
                span.set_status(trace.StatusCode.ERROR, "Bad request.")
                span.record_exception(ValueError(f"Thread with thread_id '{thread_id}' not found."))
                raise HTTPError(status_code=400, log_message=f"Thread with thread_id '{thread_id}' not found.")

            result = rq.query(
                input_=payload.input_,
                feature=feature,
                thread_id=thread_id,
                model_settings_collection=model_usage_settings,
                assistant=assistant,
            )
            messages = list(map(get_message_object, result))
            response_model = MessagesResponseModel(response=messages, meta={"model_settings": model_usage_settings.key})

            self.write(response_model.model_dump())

        except Exception as e:
            span.set_status(trace.StatusCode.ERROR, "Bad request.")
            span.record_exception(e)
            raise HTTPError(status_code=400, log_message=str(e)) from e
