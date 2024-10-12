"""This module contains the API endpoint to upload files."""

import logging
from typing import Self

from docq import manage_spaces
from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_documents import upload
from docq.manage_spaces import get_shared_space
from pydantic import ValidationError
from tornado.web import HTTPError, escape

from web.api.base_handlers import BaseRequestHandler
from web.api.utils.auth_utils import authenticated
from web.utils.streamlit_application import st_app

from .models import FileModel, SpaceFilesResponseModel

# Configuration
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "md", "docx", "pptx", "xlsx"}


def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@st_app.api_route("/api/v1/spaces/{space_id}/files/upload")
class UploadFileHandler(BaseRequestHandler):
    """Handle /api/v1/spaces/{space_id}/files/upload requests."""

    @authenticated
    def post(self: Self, space_id: int) -> None:
        """Handle POST request to upload a file.

        Upload one of more files to a space.
        """
        try:
            # print("Body:", self.request.body)

            # content_type = self.request.headers.get("Content-Type", "")
            # if content_type.startswith("multipart/form-data"):
            #     fields = cgi.FieldStorage(
            #         fp=io.BytesIO(self.request.body), headers=self.request.headers, environ={"REQUEST_METHOD": "POST"}
            #     )
            #     print("Fields:", fields)

            #     if "docq_files" in fields:
            #         file_item = fields["docq_files"]
            #         # Process the file data as it's being read
            #         while True:
            #             chunk = file_item.file.read(8192)  # Read in 8KB chunks
            #             if not chunk:
            #                 break

            if "docq_files" not in self.request.files:
                raise HTTPError(400, reason="No file part")

            files = self.request.files["docq_files"]  # 'file' is what every we want the form field to be called.
            for file_info in files:
                filename = file_info["filename"]

                if filename == "":
                    raise HTTPError(400, reason="No selected file")

                if not allowed_file(filename):
                    raise HTTPError(
                        400,
                        reason=f"File type not allowed. Allowed file types are: {', '.join(list(ALLOWED_EXTENSIONS))}",
                    )

                # Secure the filename
                filename = escape.native_str(escape.url_escape(filename))

                space = get_shared_space(space_id, self.selected_org_id)
                if not space:
                    raise HTTPError(404, reason=f"Space id {space_id} not found")

                print("Space_type:", space[7])
                space_type = SpaceType(str(space[7]).lower())

                if not space_type:
                    raise HTTPError(400, reason="Invalid space type")

                space_key = SpaceKey(
                    org_id=self.selected_org_id,
                    id_=space_id,
                    type_=space_type,
                )

                upload(filename=filename, content=file_info["body"], space=space_key)

            self.set_status(201)  # 201 Created
            self.write({"message": f"{len(files)} File(s) successfully uploaded"})
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request") from e
        except HTTPError as e:
            raise e
        except Exception as e:
            logging.error("Error: ", e)
            raise HTTPError(500, reason="Internal server error", log_message=f"Error: {str(e)}") from e


@st_app.api_route("/api/v1/spaces/{space_id}/files")
class SpaceFilesHandler(BaseRequestHandler):
    """Handle /api/v1/spaces/{space_id}/files requests."""

    @authenticated
    def get(self: Self, space_id: int) -> None:
        """Handle GET request. Get all files in a space."""
        space = get_shared_space(space_id, self.selected_org_id)
        if not space:
            raise HTTPError(404, reason=f"Space id {space_id} not found")

        print("Space_type:", space[7])
        space_type = SpaceType(str(space[7]).lower())

        space_key = SpaceKey(
            org_id=self.selected_org_id,
            id_=space_id,
            type_=space_type,
        )

        files = manage_spaces.list_documents(space_key)

        files_response = SpaceFilesResponseModel(
            response=[
                FileModel(
                    size=file.size,
                    link=file.link,
                    indexed_on=file.indexed_on,
                )
                for file in files
            ]
        )
        self.write(files_response.model_dump(by_alias=True))
