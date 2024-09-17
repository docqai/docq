"""Spaces handler endpoint for the API. /api/spaces handler."""
import logging
from typing import Optional, Self

import docq.manage_spaces as m_spaces
import docq.run_queries as rq
from docq.data_source.list import SpaceDataSources
from docq.manage_documents import upload
from pydantic import BaseModel, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import SPACE_TYPE, SpaceModel, SpacesResponseModel
from web.api.utils.auth_utils import authenticated
from web.api.utils.docq_utils import get_feature_key, get_space
from web.utils.streamlit_application import st_app


class PostRequestModel(BaseModel):
    """Post request model."""

    title: Optional[str] = None
    summary: str
    thread_id: Optional[int] = None
    space_type: SPACE_TYPE


class PostResponseModel(BaseModel):
    """Post response model."""

    # TODO: replace the use of this with SpaceResponseModel where needed.
    thread_id: Optional[int] = None
    space_value: str

def _map_to_space_model(space: tuple) -> SpaceModel:
    # [0 id , 1 org_id, 2 name, 3 summary, 4 archived, 5 datasource_type, 6 datasource_configs, 7 space_type, 8 created_at, 9 updated_at]
    return SpaceModel(
        id=space[0],
        org_id=space[1],
        name=space[2],
        summary=space[3],
        datasource_type=space[5],
        space_type=space[7],
        created_at=space[8].strftime("%Y-%m-%d %H:%M:%S"),
        updated_at=space[9].strftime("%Y-%m-%d %H:%M:%S"),
    )


@st_app.api_route("/api/v1/spaces")
class SpacesHandler(BaseRequestHandler):
    """Handle /api/v1/spaces action requests."""

    @authenticated
    def post(self: Self) -> None:
        """Handle post request: Create a thread space."""
        try:
            request = PostRequestModel.model_validate_json(self.request.body)
            feature = get_feature_key(self.current_user.uid)
            if request.space_type == "thread":
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
                    self.set_status(201)  # 201 Created
                    self.write(PostResponseModel(thread_id=thread_id, space_value=space.value()).model_dump_json())
                except Exception as e:
                    raise HTTPError(500, reason="Error creating space") from e
            elif request.space_type in ["personal", "shared", "public"]:
                # raise not implemented error
                raise HTTPError(501, reason="Not implemented")
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request") from e

    @authenticated
    def get(self: Self) -> None:
        """Handle GET request: get list of Spaces.

        query params:
            space_type: str shared, thread, public
        """
        try:
            space_type = self.get_query_argument("space_type", None)

            print("space_type", space_type)
            spaces = m_spaces.list_space(self.selected_org_id, space_type)
            print("spaces", spaces)
            space_model_list: list[SpaceModel] = [_map_to_space_model(space) for space in spaces]

            spaces_response_model = SpacesResponseModel(response=space_model_list)
            self.write(spaces_response_model.model_dump(by_alias=True))
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request") from e
        except HTTPError as e:
            raise e
        except Exception as e:
            logging.error("Error: ", e)
            raise HTTPError(500, reason="Internal server error", log_message=f"Error: {str(e)}") from e


@st_app.api_route("/api/v1/spaces/{space_id}")
class SpaceHandler(BaseRequestHandler):
    """Handle /api/space requests."""

    @authenticated
    def get(self: Self, space_id: int) -> None:
        """GET /api/v1/spaces/space_type/{space_id}."""
        space = get_space(self.selected_org_id, space_id)
        self.write(space.value())

    @authenticated
    def delete(self: Self, space_id: int) -> None:
        """DELETE /api/v1/spaces/{space_id}."""
        raise HTTPError(501, reason="Not implemented")

    @authenticated
    def update(self: Self, space_id: int) -> None:
        """UPDATE /api/v1/spaces/{space_id}."""
        raise HTTPError(501, reason="Not implemented")


@st_app.api_route("/api/v1/spaces/{space_id}/files/upload")
class SpaceFileUploadHandler(BaseRequestHandler):
    """Handle /api/spaces/{space_id}/files/upload requests."""

    __FILE_SIZE_LIMIT = 200 * 1024 * 1024
    __FILE_NAME_LIMIT = 100

    @authenticated
    def post(self: Self, space_id: int) -> None:
        """Handle POST request."""
        space = get_space(self.selected_org_id, space_id)
        fileinfo = self.request.files["filearg"][0]
        fname = fileinfo["filename"]

        if len(fileinfo["body"]) > self.__FILE_SIZE_LIMIT:
            raise HTTPError(400, reason="File too large", log_message="File size exceeds the limit")

        upload(fname[: self.__FILE_NAME_LIMIT], fileinfo["body"], space)
        self.set_status(201)  # 201 Created
        self.write(f"File {fname} is uploaded successfully.")
