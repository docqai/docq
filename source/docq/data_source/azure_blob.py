"""Data source backed by Azure Blob (container)."""

import logging as log
from typing import List

from llama_index import Document, download_loader

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
            ConfigKey("credential", "Credential", is_optional=True, is_secret=True),
        ]

    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from azure blob container."""
        AzStorageBlobReader = download_loader("AzStorageBlobReader")  # noqa: N806
        log.debug("account_url: %s", configs["account_url"])
        log.debug("container_name: %s", configs["container_name"])
        loader = AzStorageBlobReader(container_name=configs["container_name"], account_url=configs["account_url"], credential=configs["credential"])
        documents = loader.load_data()

        return documents

    def get_document_list(self, space: SpaceKey, configs: dict) -> list[tuple[str, int, int]]:
        """Get the list of documents."""
        from azure.storage.blob import ContainerClient

        try:
            container_client = ContainerClient(
                configs["account_url"], configs["container_name"], configs["credential"]
            )
            blobs_list = container_client.list_blobs()
            return list(map(lambda b: (b.name, b.last_modified, b.size), blobs_list))
        except Exception as e:
            log.error("Error listing blobs: %s", e)
            raise Exception("Ooops! something went wrong. Please check your datasource credentials and try again.") from e

