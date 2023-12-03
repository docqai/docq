"""Handle /api/rag/completion requests."""
import json
from typing import Self

from docq.domain import SpaceKey, SpaceType
from docq.model_selection.main import get_model_settings_collection
from docq.support.llm import run_ask
from llama_index import Response
from llama_index.response.schema import PydanticResponse
from tornado.web import HTTPError, RequestHandler

from web.utils.streamlit_application import st_app

from ...source.docq.manage_spaces import list_public_spaces
from .utils import authenticated


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

    def get(self: Self) -> None:
        """Handle GET request."""
        self.write({"message": "hello world 2"})

    @authenticated
    def post(self: Self) -> None:
        """Handle POST request.

        Example:
        ```shell
        curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer expected_token" -d /
        '{"input":"whats the sun?"}' http://localhost:8501/api/rag/completion
        ```
        """
        body = self.request.body
        # Parse the request body as JSON
        payload = json.loads(body)
        # Extract parameters from the JSON
        input_ = payload.get("input")
        history = payload.get("history")
        space_group_id: int = payload.get("spaceGroupId")
        org_id: int = payload.get("orgId")
        model_setting_collection_name = payload.get("modelSettingsCollectionName")
        space_keys: list[SpaceKey] = []
        if space_group_id:
            spaces = list_public_spaces(space_group_id)
            for s in spaces:
                space_keys.append(SpaceKey(id_ = s[0], type_=SpaceType.PUBLIC, org_id=org_id, summary=s[3]))

        try:
            model_usage_settings = get_model_settings_collection(model_setting_collection_name) if model_setting_collection_name else get_model_settings_collection("azure_openai_latest")
        except ValueError as e:
            raise HTTPError(400, "Invalid modelSettingsCollectionName") from e

        result = run_ask(input_=input_, history=history, model_settings_collection=model_usage_settings)

        if result:
            if isinstance(result, Response) and result.response:
                self.write(result.response)
            else:
                self.write({"error": "Response type not supported by web API"})