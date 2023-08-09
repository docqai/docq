"""Utils function for data sources."""
import logging as log
import sys
from datetime import datetime
from typing import NamedTuple, Optional

DocumentListItem = NamedTuple("DocumentListItem", [("link", str), ("indexed_on", int), ("size", int)])
"""A tuple containing information about a document. These entries are used to create the document list for rendering UI.

Attributes:
    link (str): The link to the document.
    indexed_on (int): The timestamp of when the document was indexed (epoch). Example: `datetime.timestamp(datetime.now().utcnow())`
    size (int): The size of the document in bytes."""


def create_document_list_item(document_link: str, document_text: str, indexed_on: Optional[int]) -> DocumentListItem:
    """Creates a tuple containing information about a document. These entries are used to create the document list for rendering UI.

    Args:
      document_link (str): The link to the document.
      document_text (str): The text of the document.
      indexed_on (Optional[int]): The timestamp of when the document was indexed. Defaults to `utcnow()`.

    Returns:
      DocumentListItem: A namedtuple containing the document link, indexed timestamp (epoch), and size in bytes.
    """
    dli: list[DocumentListItem] = []
    try:
        size_in_bytes = sys.getsizeof(document_text)

        size_in_bytes = size_in_bytes if size_in_bytes > 0 else 0

        if indexed_on is None:
            indexed_on = datetime.timestamp(datetime.now().utcnow())

        dli = DocumentListItem(link=document_link, indexed_on=indexed_on, size=size_in_bytes)
        log.debug("Created document list item: %s", dli)
    except Exception as e:
        log.error("Error creating document list item: %s", e)

    return dli
