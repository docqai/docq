"""Handle /api/rag/completion requests."""
from typing import Optional, Self

import docq.run_queries as rq
from docq.manage_assistants import get_assistant_fixed
from docq.manage_spaces import get_thread_space
from docq.model_selection.main import get_model_settings_collection, get_saved_model_settings_collection
from opentelemetry import trace
from pydantic import Field, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import MessagesResponseModel
from web.api.utils.docq_utils import get_feature_key, get_message_object
from web.utils.streamlit_application import st_app

from .utils.auth_utils import authenticated
from .utils.pydantic_utils import CamelModel

tracer = trace.get_tracer(__name__)


class PostRequestModel(CamelModel):
    """Pydantic model for the request body."""
    input_: str = Field(..., alias="input")
    thread_id: int
    llm_settings_collection_name: Optional[str] = Field(None)
    assistant_key: Optional[str] = Field(None)

@tracer.start_as_current_span(name="RagCompletionHandler")
@st_app.api_route("/api/v1/rag/completion")
class RagCompletionHandler(BaseRequestHandler):
    """Handle /api/v1/rag/completion requests."""

    @authenticated
    def post(self: Self) -> None:
        """Handle POST request."""
        try:
            feature = get_feature_key(self.current_user.uid)
            request_model = PostRequestModel.model_validate_json(self.request.body)
            self.thread_space = request_model.thread_id
            collection_key = request_model.llm_settings_collection_name
            model_settings_collection = get_model_settings_collection(collection_key) if collection_key else get_saved_model_settings_collection(self.selected_org_id)
            assistant_key = request_model.assistant_key if request_model.assistant_key else "default"
            assistant = get_assistant_fixed(model_settings_collection.key)[assistant_key]
            if not assistant:
                raise HTTPError(400, "Invalid assistant key")
            space = get_thread_space(self.selected_org_id, request_model.thread_id)
            if space is None:
                raise HTTPError(404, reason="Space not available")
            result = rq.query(
                input_=request_model.input_,
                feature=feature,
                thread_id=request_model.thread_id,
                model_settings_collection=model_settings_collection,
                assistant=assistant,
                spaces=[space],
            )

            if result:
                messages = list(map(get_message_object, result))
                self.write(MessagesResponseModel(response=messages).model_dump_json())
            else:
                raise HTTPError(500, "Internal server error")
        except ValidationError as e:
            raise HTTPError(400, "Invalid request body") from e
