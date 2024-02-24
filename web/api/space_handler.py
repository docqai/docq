"""Spaces handler endpoint for the API. /api/spaces handler."""
from typing import Literal, Optional, Self

import docq.manage_spaces as m_spaces
import docq.run_queries as rq
from docq.data_source.list import SpaceDataSources
from pydantic import BaseModel, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRagRequestHandler
from web.api.utils.auth_utils import authenticated
from web.utils.streamlit_application import st_app

from ...source.docq.config import SpaceType


class PostRequestModel(BaseModel):
    """Post request model."""
    title: str
    summary: str
    space_type: Literal[
        "personal", "shared", "public", "thread"
    ]  # don't think we want to bind this to the backend enum, for the same reason that we don't use the same models here.
    thread_id: Optional[int] = None

class PostResponseModel(BaseModel):
    """Post response model."""

    thread_id: Optional[int] = None
    space_value: str

@st_app.api_route("/api/spaces")
class SpacesHandler(BaseRagRequestHandler):
    """Handle /api/space requests."""

    @authenticated
    def post(self: Self) -> None:
        """Handle post request: Create a thread space."""
        try:
            request = PostRequestModel.model_validate_json(self.request.body)

            if request.space_type == "thread":
                try:
                    thread_id = (
                        request.thread_id
                        if request.thread_id
                        else rq.create_history_thread(request.title, self.feature)
                    )
                    space = m_spaces.create_thread_space(
                        self.selected_org_id,
                        thread_id,
                        request.summary,
                        SpaceDataSources.MANUAL_UPLOAD.name,
                    )
                    self.write(PostResponseModel(thread_id=thread_id, space_value=space.value()).model_dump_json())
                except Exception as e:
                    raise HTTPError(500, reason="Internal server error") from e
            elif request.space_type in ["personal", "shared", "public"]:
                # raise not implemented error
                raise HTTPError(501, reason="Not implemented")
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request") from e


@st_app.api_route("/api/spaces/{space_id}")
class SpaceHandler(BaseRagRequestHandler):
    """Handle /api/space requests."""

    @authenticated
    def get(self: Self, space_id) -> None:
        """GET /api/spaces/{space_id}."""
        self.write(self.space.value())
