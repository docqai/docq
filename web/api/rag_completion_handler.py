"""Handle /api/rag/completion requests."""
import logging
from typing import Optional, Self

import docq.run_queries as rq
from docq import manage_spaces
from docq.config import OrganisationFeatureType, SpaceType
from docq.domain import FeatureKey, SpaceKey
from docq.manage_assistants import get_assistant_or_default
from docq.manage_spaces import get_shared_spaces
from docq.model_selection.main import get_model_settings_collection
from opentelemetry import trace
from pydantic import Field, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import MessagesResponseModel
from web.api.utils.docq_utils import get_message_object
from web.utils.streamlit_application import st_app

from .utils.auth_utils import authenticated
from .utils.pydantic_utils import CamelModel

tracer = trace.get_tracer(__name__)


class PostRequestModel(CamelModel):
    """Pydantic model for the RAG completion request."""

    input_: str = Field(..., alias="input")
    thread_id: int
    assistant_scoped_id: str
    space_ids: Optional[list[int]] = Field(None)  # for now only shared spaces are supported


@tracer.start_as_current_span(name="RagCompletionHandler")
@st_app.api_route("/api/v1/rag/completion")
class RagCompletionHandler(BaseRequestHandler):
    """Handle /api/v1/rag/completion requests."""

    @authenticated
    def post(self: Self) -> None:
        """Handle RAG completion request."""
        try:
            feature = FeatureKey(
                type_=OrganisationFeatureType.ASK_SHARED, id_=self.current_user.uid
            )  # get_feature_key(self.current_user.uid)
            # request_json = json.loads(self.request.body)
            request_model = PostRequestModel.model_validate_json(self.request.body)
            print("request_model:", request_model)

            if request_model.assistant_scoped_id:
                # assistant = get_assistant_fixed(model_settings_collection.key)[assistant_key]
                assistant = get_assistant_or_default(request_model.assistant_scoped_id, self.selected_org_id)

            if not assistant:
                raise HTTPError(400, reason="Invalid assistant_scoped_id")

            space_exists = manage_spaces.thread_space_exists(thread_id=request_model.thread_id)

            thread_space = None
            if space_exists:
                # space exists globally, check if it's in this org_id
                thread_space = manage_spaces.get_thread_space(self.selected_org_id, request_model.thread_id)

            # thread_space = get_thread_space(self.selected_org_id, request_model.thread_id)

            if thread_space is None:
                raise HTTPError(404, reason="This threads Thread Space not available")

            space_keys = []
            if request_model.space_ids:
                spaces = get_shared_spaces(space_ids=request_model.space_ids)
                space_keys = [SpaceKey(id_=space[0], org_id=space[1], type_=SpaceType.SHARED) for space in spaces]

            print("space_keys:", space_keys)
            if not manage_spaces.is_space_empty(thread_space):
                # is empty i.e. no docs then theirs no index so ignore thread_space
                space_keys.append(thread_space)

            model_settings_collection = get_model_settings_collection(assistant.llm_settings_collection_key)

            result = rq.query(
                input_=request_model.input_,
                feature=feature,
                thread_id=request_model.thread_id,
                model_settings_collection=model_settings_collection,
                assistant=assistant,
                spaces=space_keys,
            )

            if result:
                messages = list(map(get_message_object, result))
                self.write(MessagesResponseModel(response=messages).model_dump(by_alias=True))
            else:
                raise HTTPError(500, reason="Internal server error", log_message="Internal server error")
        except ValidationError as e:
            logging.error("ValidationError:", e)
            raise HTTPError(
                400,
                reason="Invalid request body",
                log_message=f"POST payload failed request model Pydantic validation. Error: {e}",
            ) from e
        except ValueError as e:
            logging.error("ValueError:", e)
            raise HTTPError(400, reason=f"Bad request. {e}", log_message=str(e)) from e
        except Exception as e:
            logging.error("Exception:", e)
            raise HTTPError(500, reason="Internal server error", log_message=str(e)) from e
