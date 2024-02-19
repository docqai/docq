"""GET /api/top-questions?size=x&thread_id=y."""

from typing import Self

from web.api.base import BaseRagRequestHandler
from web.api.utils import authenticated
from web.utils.streamlit_application import st_app


@st_app.api_route(r"/api/top-questions")
class FileUploadHandler(BaseRagRequestHandler):
    """Handle GET /api/top-questions requests.

    Query Parameters:
        thread_id: int (required) - The thread id.
    """

    @authenticated
    def get(self: Self) -> None:
        """Handle GET top questions request."""
        thread_id = self.get_argument("thread_id")
