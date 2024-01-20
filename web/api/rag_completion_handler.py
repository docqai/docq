"""Handle /api/rag/completion requests."""
from typing import Optional, Self

from docq.domain import SpaceKey, SpaceType
from docq.manage_spaces import list_public_spaces
from docq.model_selection.main import get_model_settings_collection
from docq.support.llm import run_ask
from llama_index import Response
from pydantic import Field, ValidationError
from tornado.web import HTTPError, RequestHandler

from web.utils.streamlit_application import st_app

from .utils import CamelModel, authenticated


class PostRequestModel(CamelModel):
    """Pydantic model for the request body."""
    input_: str = Field(..., alias="input")
    history: Optional[str] = None
    space_group_id: Optional[int] = Field(None)
    org_id: Optional[int] = Field(None)
    model_settings_collection_name: Optional[str] = Field(None)


class PostResponseModel(CamelModel):
    """Pydantic model for the response body."""
    response: str


@st_app.api_route("/api/rag/completion")
class RagCompletionHandler(RequestHandler):
    """Handle /api/rag/completion requests."""

    def check_origin(self: Self, origin) -> bool:
        """Override the origin check if it's causing problems."""
        return True

    def check_xsrf_cookie(self) -> bool:
        # If `True`, POST, PUT, and DELETE are block unless the `_xsrf` cookie is set.
        # Safe with token based authN
        return False

    @authenticated
    def post(self: Self) -> None:
        """Handle POST request."""
        body = self.request.body
        try:
            request_model = PostRequestModel.model_validate_json(body)

            space_keys: list[SpaceKey] = []
            if request_model.space_group_id:
                spaces = list_public_spaces(request_model.space_group_id)
                for s in spaces:
                    space_keys.append(SpaceKey(id_ = s[0], type_=SpaceType.PUBLIC, org_id=request_model.org_id if request_model.org_id else 0, summary=s[3]))

            try:
                model_usage_settings = get_model_settings_collection(request_model.model_settings_collection_name) if request_model.model_settings_collection_name else get_model_settings_collection("azure_openai_latest")
            except ValueError as e:
                raise HTTPError(400, "Invalid modelSettingsCollectionName") from e

            history = request_model.history if request_model.history else ""
            result = run_ask(input_=request_model.input_, history=history, model_settings_collection=model_usage_settings)

            if result:
                if isinstance(result, Response) and result.response:
                    response_model = PostResponseModel(response=result.response)
                    # Dump the model to a dictionary
                    self.write(response_model.model_dump())
                else:
                    self.write({"error": "Response type not supported by web API"})
        except ValidationError as e:
            raise HTTPError(400, "Invalid request body") from e


