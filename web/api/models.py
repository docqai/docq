"""API models."""

from typing import Optional

from pydantic import BaseModel, Field


class UserModel(BaseModel):
    """Pydantic model for user data."""

    uid: int
    fullname: str
    super_admin: bool
    username: str

class MessageModel(BaseModel):
    """Pydantic model for message data."""
    id_: int = Field(..., alias="id")
    message: str
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
