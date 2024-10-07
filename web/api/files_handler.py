"""This module contains the API endpoint to upload files."""

import logging
from typing import Self

from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_documents import upload
from pydantic import ValidationError
from tornado.web import HTTPError, escape

from web.api.base_handlers import BaseRequestHandler
from web.api.models import FileUploadRequestModel
from web.api.utils.auth_utils import authenticated
from web.utils.streamlit_application import st_app

# Configuration
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "md", "docx", "pptx", "xlsx"}


def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@st_app.api_route("/api/v1/files/{}/upload")
class UploadFileHandler(BaseRequestHandler):
    """Handle /api/v1/files/upload requests."""

    @authenticated
    def post(self: Self) -> None:
        """Handle POST request to upload a file.

        Upload one of more files to a space.
        """
        try:
            requestPayload = FileUploadRequestModel.model_validate_json(self.request.body)
            if "file" not in self.request.files:
                raise HTTPError(400, reason="No file part")

            files = self.request.files["file"]
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
                space_type = SpaceType(requestPayload.space_type)

                if not space_type:
                    raise HTTPError(400, reason="Invalid space type")

                space_key = SpaceKey(
                    org_id=self.selected_org_id,
                    id_=requestPayload.space_id,
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
