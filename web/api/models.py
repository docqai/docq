"""API models."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

SPACE_TYPE = Literal["personal", "shared", "public", "thread"]
FEATURE = Literal["rag", "chat"]

class UserModel(BaseModel):
    """Pydantic model for user data."""

    uid: int
    fullname: str
    super_admin: bool
    username: str

class MessageModel(BaseModel):
    """Pydantic model for message data."""
    id_: int = Field(..., alias="id")
    content: str
    human: bool
    timestamp: str
    thread_id: int

class MessageResponseModel(BaseModel):
    """Pydantic model for the response body."""
    response: list[MessageModel]
    meta: Optional[dict[str,str]] = None

class ChatHistoryModel(BaseModel):
    """Pydantic model for chat history."""
    response : list[MessageModel]

class ThreadModel(BaseModel):
    """Pydantic model for the response body."""
    id_: int = Field(..., alias="id")
    topic: str
    created_at: str

class SpaceModel(BaseModel):
    """Pydantic model for the response body."""
    id_: int = Field(..., alias="id")
    space_type: SPACE_TYPE
    created_at: str

class ThreadResponseModel(BaseModel):
    """Pydantic model for the response body."""
    response: list[ThreadModel]

class ThreadPostRequestModel(BaseModel):
    """Pydantic model for the request body."""
    topic: str
