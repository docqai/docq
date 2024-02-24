"""Handle /api/rag/completion requests."""
from typing import Optional, Self

import docq.run_queries as rq
from docq.manage_assistants import get_personas_fixed
from docq.model_selection.main import get_model_settings_collection, get_saved_model_settings_collection
from pydantic import Field, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRagRequestHandler
from web.api.models import MessageModel, MessageResponseModel
from web.utils.streamlit_application import st_app

from .utils.auth_utils import authenticated
from .utils.pydantic_utils import CamelModel


class PostRequestModel(CamelModel):
    """Pydantic model for the request body."""
    input_: str = Field(..., alias="input")
    thread_id: int
    llm_settings_collection_name: Optional[str] = Field(None)
    persona_key: Optional[str] = Field(None)


class PostResponseModel(CamelModel):
    """Pydantic model for the response body."""
    response: str


@st_app.api_route("/api/rag/completion")
class RagCompletionHandler(BaseRagRequestHandler):
    """Handle /api/rag/completion requests."""

    @authenticated
    def post(self: Self) -> None:
        """Handle POST request."""
        body = self.request.body
        try:
            request_model = PostRequestModel.model_validate_json(body)
            collection_key = request_model.llm_settings_collection_name
            model_settings_collection = get_model_settings_collection(collection_key) if collection_key else get_saved_model_settings_collection(self.selected_org_id)
            persona = get_personas_fixed()[request_model.persona_key] if request_model.persona_key else get_personas_fixed().get("default")
            if not persona:
                raise HTTPError(400, "Invalid persona key")
            result = rq.query(
                input_=request_model.input_,
                feature=self.feature,
                thread_id=request_model.thread_id,
                model_settings_collection=model_settings_collection,
                persona=persona,
                spaces=[self.space],
            )

            if result:
                messages = [MessageModel(**self._get_message_object(msg)) for msg in result]
                self.write(MessageResponseModel(response=messages).model_dump_json())
            else:
                raise HTTPError(500, "Internal server error")
        except ValidationError as e:
            raise HTTPError(400, "Invalid request body") from e
