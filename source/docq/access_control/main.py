"""Access control for Docq."""

from dataclasses import dataclass
from enum import Enum


class SpaceAccessType(Enum):
    """Space access types."""

    USER = "By User"
    GROUP = "By Group"
    PUBLIC = "Public Access"


@dataclass
class SpaceAccessor:
    """Space accessor."""

    type_: SpaceAccessType
    accessor_id: int = None
    accessor_name: str = None
