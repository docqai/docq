"""Spaces handler endpoint for the API. /api/spaces handler."""
from typing import Optional, Self

import docq.manage_spaces as m_spaces
import docq.run_queries as rq
from docq.data_source.list import SpaceDataSources
from pydantic import BaseModel, ValidationError
from tornado.web import HTTPError

from web.api.base import BaseRagRequestHandler
from web.api.utils import authenticated
from web.utils.streamlit_application import st_app


class PostRequestModel(BaseModel):
    """Post request model."""
    title: str
    summary: str
    thread_id: Optional[int] = None

@st_app.api_route(r"/api/space")
class FileUploadHandler(BaseRagRequestHandler):
    """Handle /api/space requests."""

    @authenticated
    def get(self: Self) -> None:
        """GET /api/space?thread_id=x."""
        self.write(self.space.value())

    @authenticated
    def post(self: Self) -> None:
        """Handle post request: Create a thread space."""
        try:
            data = PostRequestModel.model_validate_json(self.request.body)
            try:
                thread_id = data.thread_id if data.thread_id else rq.create_history_thread(data.title, self.feature)
                space = m_spaces.create_thread_space(
                    self.selected_org_id, thread_id, data.summary, SpaceDataSources.MANUAL_UPLOAD.name,
                )
                self.write(space.value())
            except Exception as e:
                raise HTTPError(500, reason="Internal server error") from e
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request") from e
