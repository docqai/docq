"""Access control for Docq."""

from enum import Enum


class SpaceAccessType(Enum):
    """Space access types."""

    USER = "By User"
    GROUP = "By Group"
    PUBLIC = "Public Access"
