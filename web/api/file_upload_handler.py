"""File upload handler /api/file/upload."""
from typing import Self

import docq.manage_documents as m_documents

from web.api.base_handlers import BaseRagRequestHandler
from web.api.utils import authenticated
from web.utils.streamlit_application import st_app


@st_app.api_route(r"/api/file/upload")
class FileUploadHandler(BaseRagRequestHandler):
    """Handle /api/file/upload requests.

    Query Parameters:
        thread_id: int (required) - The thread id.
    """

    @authenticated
    def post(self: Self) -> None:
        """Handle POST request."""
        fileinfo = self.request.files['filearg'][0]
        fname = fileinfo['filename']
        m_documents.upload(fname, fileinfo['body'], self.space)
        self.write(f"File {fname} is uploaded successfully.")
