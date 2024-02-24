"""Domain classes for Docq."""
import logging as log
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Self

from .config import OrganisationFeatureType, SpaceType

_SEPARATOR_FOR_STR = ":"
_SEPARATOR_FOR_VALUE = "_"
_DEFAULT_SEPARATOR = _SEPARATOR_FOR_STR


def _join_properties(separator: str = _DEFAULT_SEPARATOR, *args: Optional[Any]) -> str:
    return separator.join([str(arg) for arg in args])


@dataclass
class FeatureKey:
    """Feature key."""

    type_: OrganisationFeatureType
    id_: int

    def __str__(self: Self) -> str:
        """Returns the string representation of the feature key."""
        return _join_properties(_SEPARATOR_FOR_STR, self.type_.name, self.id_)

    def value(self: Self) -> str:
        """Feature key value."""
        return _join_properties(_SEPARATOR_FOR_VALUE, self.type_.name, self.id_)


@dataclass
class SpaceKey:
    """Space key."""

    type_: SpaceType
    id_: int
    org_id: int
    """The organisation ID that owns the space."""
    summary: Optional[str] = None


    def __str__(self: Self) -> str:
        """Returns the string representation of the space key."""
        return _join_properties(_SEPARATOR_FOR_STR, self.type_.name, self.org_id, self.id_)

    def value(self: Self) -> str:
        """Space key value."""
        return _join_properties(_SEPARATOR_FOR_VALUE, self.type_.name, self.org_id, self.id_)


@dataclass
class ConfigKey:
    """Config key."""

    key: str
    name: str
    is_optional: bool = False
    is_secret: bool = False
    ref_link: Optional[str] = None
    options: Optional[dict] = None


@dataclass
class DocumentListItem:
    """Data about a document item in a list. These entries are used to create the document list for rendering UI.

    Args:
        link (str): The link to the document.
        indexed_on (int): The timestamp of when the document was indexed.
        size (int): The size of the document in bytes.
    """

    link: str
    indexed_on: int
    size: int

    @staticmethod
    def create_instance(document_link: str, document_text: str, indexed_on: Optional[int] = None) -> "DocumentListItem":
        """Creates a tuple containing information about a document.

        Args:
        document_link (str): The link to the document.
        document_text (str): The text of the document.
        indexed_on (Optional[int]): The timestamp of when the document was indexed. Defaults to `utcnow()`.

        Returns:
        DocumentListItem: A namedtuple containing the document link, indexed timestamp (epoch), and size in bytes.
        """
        try:
            size_in_bytes = sys.getsizeof(document_text)

            size_in_bytes = size_in_bytes if size_in_bytes > 0 else 0

            if indexed_on is None:
                indexed_on = int(datetime.timestamp(datetime.now().utcnow()))

            item = DocumentListItem(document_link, indexed_on, size_in_bytes)
            log.debug("Created document list item: %s", item)
            return item
        except Exception as e:
            log.error(
                "Error creating document list item with '%s', '%s', '%d'", document_link, document_text, indexed_on
            )
            raise e

@dataclass
class Persona:
    """A persona is system prompt and user prompt template that represent a particular persona we want an LLM to emulate."""

    key: str
    """Unique ID for a Persona instance"""
    name: str
    """Friendly name for the persona"""
    system_prompt_content: str
    user_prompt_template_content: str


class PersonaType(Enum):
    """Persona type."""

    SIMPLE_CHAT = "Simple Chat"
    AGENT = "Agent"
    ASK = "Ask"
