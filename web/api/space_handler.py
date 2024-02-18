"""Spaces handler endpoint for the API. /api/spaces handler."""
from typing import Optional, Self

import docq.manage_organisations as m_orgs
import docq.manage_spaces as m_spaces
import docq.run_queries as rq
from docq.config import SpaceType
from docq.data_source.list import SpaceDataSources
from docq.domain import FeatureKey, OrganisationFeatureType, SpaceKey
from pydantic import BaseModel, ValidationError
from tornado.web import HTTPError

from web.api.utils import BaseRequestHandler, authenticated
from web.utils.handlers import _default_org_id as get_default_org_id
from web.utils.streamlit_application import st_app


class PostRequestModel(BaseModel):
    """Post request model."""
    title: str
    summary: str
    thread_id: Optional[int] = None

@st_app.api_route(r"/api/space")
class FileUploadHandler(BaseRequestHandler):
    """Handle /api/space requests."""

    __selected_org_id: Optional[int] = None

    @property
    def selected_org_id(self: Self) -> int:
        """Get the selected org id."""
        if self.__selected_org_id is None:
            u = self.current_user
            member_orgs = m_orgs.list_organisations(user_id=self.current_user.uid)
            self.__selected_org_id = get_default_org_id(member_orgs, (u.uid, u.fullname, u.super_admin, u.username))
        return self.__selected_org_id

    @property
    def feature(self: Self) -> FeatureKey:
        """Get the feature key."""
        return FeatureKey(OrganisationFeatureType.ASK_SHARED, self.current_user.uid)

    @property
    def space(self: Self) -> SpaceKey:
        """Get the space key."""
        if self.selected_org_id is None:
            raise HTTPError(401, "User is not a member of any organisation.")
        user_id = self.current_user.uid
        summary = self.get_argument("summary", None)
        return SpaceKey(SpaceType.THREAD, int(user_id), org_id=self.selected_org_id, summary=summary)

    @authenticated
    def get(self: Self) -> None:
        """Handle GET request."""
        thread_id = self.get_argument("thread_id")
        space = m_spaces.get_thread_space(self.selected_org_id, int(thread_id))
        if space is None:
            raise HTTPError(404, reason="Space Not found")
        self.write(space.value())

    @authenticated
    def post(self: Self) -> None:
        """Handle post request: Create a thread space."""
        try:
            data = PostRequestModel.model_validate_json(self.request.body)
            try:
                thread_id = data.thread_id if data.thread_id else rq.create_history_thread(data.title, self.feature)
                m_spaces.create_thread_space(
                    self.selected_org_id, thread_id, data.summary, SpaceDataSources.MANUAL_UPLOAD.name,
                )
            except Exception as e:
                raise HTTPError(500, reason="Internal server error") from e
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request") from e




