"""Domain classes for Docq."""

import logging as log
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from .config import FeatureType, SpaceType

_SEPARATOR_FOR_STR = ":"
_SEPARATOR_FOR_VALUE = "_"
_DEFAULT_SEPARATOR = _SEPARATOR_FOR_STR


def _join_properties(separator: str = _DEFAULT_SEPARATOR, *args: Optional[Any]) -> str:
    return separator.join([str(arg) for arg in args])


@dataclass
class FeatureKey:
    """Feature key."""

    type_: FeatureType
    id_: int

    def __str__(self) -> str:
        return _join_properties(_SEPARATOR_FOR_STR, self.type_.name, self.id_)

    def value(self) -> str:
        return _join_properties(_SEPARATOR_FOR_VALUE, self.type_.name, self.id_)


@dataclass
class SpaceKey:
    """Space key."""

    type_: SpaceType
    id_: int

    def __str__(self) -> str:
        return _join_properties(_SEPARATOR_FOR_STR, self.type_.name, self.id_)

    def value(self) -> str:
        return _join_properties(_SEPARATOR_FOR_VALUE, self.type_.name, self.id_)


@dataclass
class ConfigKey:
    """Config key."""

    key: str
    name: str
    is_optional: bool = False
    is_secret: bool = False
    ref_link: str = None


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
    def create_instance(document_link: str, document_text: str, indexed_on: int = None) -> "DocumentListItem":
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
                indexed_on = datetime.timestamp(datetime.now().utcnow())

            item = DocumentListItem(document_link, size_in_bytes, indexed_on)
            log.debug("Created document list item: %s", item)
            return item
        except Exception as e:
            log.error(
                "Error creating document list item with '%s', '%s', '%d'", document_link, document_text, indexed_on
            )
            raise e
