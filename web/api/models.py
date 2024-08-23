"""API models."""

from abc import ABC
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from .utils.pydantic_utils import CamelModel

SPACE_TYPE = Literal["PERSONAL", "SHARED", "PUBLIC", "THREAD"]
FEATURE = Literal["rag", "chat"]

class UserModel(BaseModel):
    """Pydantic model for a user data."""

    uid: int
    fullname: str
    super_admin: bool
    username: str

class MessageModel(CamelModel):
    """Pydantic model for a message data."""

    id_: int = Field(..., alias="id")
    content: str
    human: bool
    timestamp: str
    thread_id: int


class ThreadModel(CamelModel):
    """Model for a Thread."""

    id_: int = Field(..., alias="id")
    topic: str
    created_at: str


class ThreadHistoryModel(CamelModel):
    """Model for a Thread with it's history messages."""

    messages: list[MessageModel]


class SpaceModel(CamelModel):
    """Model for a Space."""

    id_: int = Field(..., alias="id", serialization_alias="id")
    org_id: int
    name: str
    summary: str
    datasource_type: str
    space_type: SPACE_TYPE
    created_at: str
    updated_at: str


class BaseResponseModel(CamelModel, ABC):
    """All HTTP API response models should inherit from this class."""

    response: Any


class MessagesResponseModel(BaseResponseModel):
    """HTTP response model for a **list** of Message."""

    response: list[MessageModel]
    meta: Optional[dict[str, str]] = None


class ThreadsResponseModel(BaseResponseModel):
    """HTTP response model for a **list** of Thread."""

    response: list[ThreadModel]

class ThreadResponseModel(BaseResponseModel):
    """HTTP response model for a single Thread."""

    response: ThreadModel


class ThreadHistoryResponseModel(BaseResponseModel):
    """HTTP response model for a single Thread with history messages."""

    response: ThreadHistoryModel


class SpaceResponseModel(BaseResponseModel):
    """HTTP response model for a single Space."""

    response: SpaceModel


class SpacesResponseModel(BaseResponseModel):
    """HTTP response model for a **list** of Space."""

    response: list[SpaceModel]


class ThreadPostRequestModel(CamelModel):
    """Pydantic model for the request body."""
    topic: str
