import uuid
from dataclasses import asdict, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, Union

from pydantic.dataclasses import dataclass


@dataclass
class Message(object):
    user_id: str
    role: str
    content: str
    root_msg_id: Optional[str] = None
    msg_id: Optional[str] = None
    timestamp: Optional[str] = None
    personalize: Optional[bool] = False
    ra: Optional[str] = None
    code: Optional[str] = None
    metadata: Optional[Any] = None
    session_id: Optional[str] = None

    def __post_init__(self):
        if self.msg_id is None:
            self.msg_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def dict(self):
        result = asdict(self)
        return result


@dataclass
class Skill(object):
    title: str
    file_name: str
    content: str
    id: Optional[str] = None
    description: Optional[str] = None
    timestamp: Optional[str] = None
    user_id: Optional[str] = None

    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.user_id is None:
            self.user_id = "default"

    def dict(self):
        result = asdict(self)
        return result


# web api data models


# autogenflow data models
@dataclass
class ModelConfig:
    """Data model for Model Config item in LLMConfig for Autogen."""

    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_type: Optional[str] = None
    api_version: Optional[str] = None


@dataclass
class LLMConfig:
    """Data model for LLM Config for Autogen."""

    config_list: List[Any] = field(default_factory=List)
    temperature: float = 0
    cache_seed: Optional[Union[int, None]] = None
    timeout: Optional[int] = None


@dataclass
class AgentConfig:
    """Data model for Agent Config for Autogen."""

    name: str
    llm_config: Optional[Union[LLMConfig, bool]] = False
    human_input_mode: str = "NEVER"
    max_consecutive_auto_reply: int = 10
    system_message: Optional[str] = None
    is_termination_msg: Optional[Union[bool, str, Callable]] = None
    code_execution_config: Optional[Union[bool, str, Dict[str, Any]]] = None


