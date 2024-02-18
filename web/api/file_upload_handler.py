"""File upload handler /api/file/upload."""
import os
import uuid
from typing import List, Self

import docq.manage_documents as m_documents
import docq.manage_spaces as m_spaces
import docq.run_queries as rq
from docq.config import SpaceType
from docq.domain import FeatureKey, OrganisationFeatureType, SpaceKey

from web.api.utils import BaseRequestHandler, authenticated
from web.utils.streamlit_application import st_app


@st_app.api_route(r"/api/file/upload")
class FileUploadHandler(BaseRequestHandler):
    """Handle /api/file/upload requests."""

    @property
    def feature(self: Self) -> FeatureKey:
        """Get the feature key."""
        return FeatureKey(OrganisationFeatureType.ASK_SHARED, self.current_user.uid)

    @property
    def space(self: Self) -> SpaceKey:
        """Get the space key."""
        user_id = self.current_user.uid
        org_id = self.get_argument("selected_org_id")
        summary = self.get_argument("summary", None)

        return SpaceKey(SpaceType.THREAD, int(user_id), org_id=int(org_id), summary=summary)

    @authenticated
    def post(self: Self) -> None:
        """Handle POST request."""
        fileinfo = self.request.files['filearg'][0]
        fname = fileinfo['filename']
        extn = os.path.splitext(fname)[1]
        cname = str(uuid.uuid4()) + extn
        fh = open(f"files/{cname}", 'wb')
        fh.write(fileinfo['body'])
        self.write(f"/api/file/{cname}")