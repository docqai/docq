"""Data source backed by Azure Blob Storage."""

from typing import List

from llama_index import Document

from ..domain import SpaceKey
from .main import SpaceDataSource


class AzureBlobStorage(SpaceDataSource):
    """Space with data from Azure Blob Storage."""

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("Azure Blob")

    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from the data source."""
        # TODO: use azure blob storage to load the documents
        pass
