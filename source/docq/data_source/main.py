"""Data source for Docq."""

from abc import ABC, abstractmethod
from typing import List

from llama_index import Document

from ..domain import SpaceKey
from .azure_blob_storage import AzureBlobStorage
from .manual_upload import ManualUpload


class SpaceDataSource(ABC):
    """Abstract definition of the data source for a space. To be extended by concrete data sources."""

    def __init__(self, name: str) -> None:
        """Initialize the data source."""
        self.name = name

    def get_name(self) -> str:
        """Get the name of the data source."""
        return self.name

    @abstractmethod
    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from the data source."""
        pass


SPACE_DATA_SOURCES = {
    "MANUAL_UPLOAD": ManualUpload(),
    "AZURE_BLOB_STORAGE": AzureBlobStorage(),
}
