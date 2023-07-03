"""Data source backed by Azure Blob (container)."""

from typing import List

from llama_index import Document

from ..domain import ConfigKey, SpaceKey
from .main import SpaceDataSource


class AzureBlob(SpaceDataSource):
    """Space with data from Azure Blob."""

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("Azure Blob")

    def get_config_keys(self) -> List[ConfigKey]:
        """Get the config keys for azure blob container."""
        return [
            ConfigKey("account_url", "Storage Account URL"),
            ConfigKey("container_name", "Blob Container Name"),
        ]

    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from azure blob container."""
        # TODO: use azure blob container to load the documents
        pass
