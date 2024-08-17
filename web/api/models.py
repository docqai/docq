"""API models."""

from abc import ABC
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

SPACE_TYPE = Literal["personal", "shared", "public", "thread"]
FEATURE = Literal["rag", "chat"]

class UserModel(BaseModel):
    """Pydantic model for a user data."""

    uid: int
    fullname: str
    super_admin: bool
    username: str

class MessageModel(BaseModel):
    """Pydantic model for a message data."""

    id_: int = Field(..., alias="id")
    content: str
    human: bool
    timestamp: str
    thread_id: int


class ThreadModel(BaseModel):
    """Model for a Thread."""

    id_: int = Field(..., alias="id")
    topic: str
    created_at: str


class ThreadHistoryModel(ThreadModel):
    """Model for a Thread with it's history messages."""

    messages: list[MessageModel]


class SpaceModel(BaseModel):
    """Pydantic model for the response body."""
    id_: int = Field(..., alias="id")
    space_type: SPACE_TYPE
    created_at: str


class BaseResponseModel(BaseModel, ABC):
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


class ThreadPostRequestModel(BaseModel):
    """Pydantic model for the request body."""
    topic: str
