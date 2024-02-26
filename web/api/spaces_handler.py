"""Spaces handler endpoint for the API. /api/spaces handler."""
from typing import Optional, Self

import docq.manage_spaces as m_spaces
import docq.run_queries as rq
from docq.data_source.list import SpaceDataSources
from docq.manage_documents import upload
from pydantic import BaseModel, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import SPACE_TYPE
from web.api.utils.auth_utils import authenticated
from web.api.utils.docq_utils import get_feature_key, get_space
from web.utils.streamlit_application import st_app


class PostRequestModel(BaseModel):
    """Post request model."""

    title: Optional[str] = None
    summary: str
    thread_id: Optional[int] = None


class PostResponseModel(BaseModel):
    """Post response model."""

    thread_id: Optional[int] = None
    space_value: str


@st_app.api_route("/api/v1/spaces/{space_type}")
class SpacesHandler(BaseRequestHandler):
    """Handle /api/spaces requests."""

    @authenticated
    def post(self: Self, space_type: SPACE_TYPE) -> None:
        """Handle post request: Create a thread space."""
        try:
            request = PostRequestModel.model_validate_json(self.request.body)
            feature = get_feature_key(self.current_user.uid)
            if space_type == "thread":
                try:
                    thread_id = (
                        request.thread_id
                        if request.thread_id
                        else rq.create_history_thread(request.title or "New thread", feature)
                    )
                    space = m_spaces.create_thread_space(
                        self.selected_org_id,
                        thread_id,
                        request.summary,
                        SpaceDataSources.MANUAL_UPLOAD.name,
                    )
                    self.write(PostResponseModel(thread_id=thread_id, space_value=space.value()).model_dump_json())
                except Exception as e:
                    raise HTTPError(500, reason="Error creating space") from e
            elif space_type in ["personal", "shared", "public"]:
                # raise not implemented error
                raise HTTPError(501, reason="Not implemented")
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request") from e


@st_app.api_route("/api/v1/spaces/{space_type}/{space_id}")
class SpaceHandler(BaseRequestHandler):
    """Handle /api/space requests."""

    @authenticated
    def get(self: Self, space_type: SPACE_TYPE, space_id: int) -> None:
        """GET /api/v1/spaces/space_type/{space_id}."""
        space = get_space(self.selected_org_id, space_id, space_type)
        self.write(space.value())

    @authenticated
    def delete(self: Self, space_type: SPACE_TYPE, space_id: int) -> None:
        """DELETE /api/v1/spaces/space_type/{space_id}."""
        raise HTTPError(501, reason="Not implemented")

    @authenticated
    def update(self: Self, space_type: SPACE_TYPE, space_id: int) -> None:
        """UPDATE /api/v1/spaces/space_type/{space_id}."""
        raise HTTPError(501, reason="Not implemented")


@st_app.api_route("/api/v1/spaces/{space_type}/{space_id}/files/upload")
class SpaceFileUploadHandler(BaseRequestHandler):
    """Handle /api/spaces/{space_id}/files/upload requests."""

    __FILE_SIZE_LIMIT = 200 * 1024 * 1024
    __FILE_NAME_LIMIT = 100

    @authenticated
    def post(self: Self, space_type: SPACE_TYPE, space_id: int) -> None:
        """Handle POST request."""
        space = get_space(self.selected_org_id, space_id, space_type)
        fileinfo = self.request.files["filearg"][0]
        fname = fileinfo["filename"]

        if len(fileinfo["body"]) > self.__FILE_SIZE_LIMIT:
            raise HTTPError(400, reason="File too large", log_message="File size exceeds the limit")

        upload(fname[: self.__FILE_NAME_LIMIT], fileinfo["body"], space)
        self.write(f"File {fname} is uploaded successfully.")
