"""Data source backed by Azure Blob (container)."""

import logging as log
from datetime import datetime
from typing import List
from urllib.parse import urlparse

from llama_index import Document

from ..domain import ConfigKey, SpaceKey
from ..support.store import get_index_dir
from .main import DocumentMetadata, SpaceDataSourceFileBased
from .support.opendal_reader.base import OpendalReader


class AzureBlob(SpaceDataSourceFileBased):
    """Space with data from Azure Blob."""

    _DOCUMENT_LIST_FILENAME = "document_list.json"

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("Azure Blob")

    def get_config_keys(self) -> List[ConfigKey]:
        """Get the config keys for azure blob container."""
        return [
            ConfigKey(
                "account_url",
                "Storage Account URL",
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-azure-blob-container",
            ),
            ConfigKey(
                "container_name",
                "Blob Container Name",
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-azure-blob-container",
            ),
            ConfigKey(
                "credential",
                "Credential",
                is_optional=True,
                is_secret=True,
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-azure-blob-container",
            ),
        ]

    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from azure blob container."""

        def lambda_metadata(x: str) -> dict:
            return {
                str(DocumentMetadata.FILE_PATH.name).lower(): x,
                str(DocumentMetadata.SPACE_ID.name).lower(): space.id_,
                str(DocumentMetadata.SPACE_TYPE.name).lower(): space.type_.name,
                str(DocumentMetadata.DATA_SOURCE_NAME.name).lower(): self.get_name(),
                str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower(): self.__class__.__base__.__name__,
                str(DocumentMetadata.SOURCE_URI.name).lower(): x,
                str(DocumentMetadata.INDEXED_ON.name).lower(): datetime.timestamp(datetime.now().utcnow()),
            }

        log.debug("account_url: %s", configs["account_url"])
        log.debug("container_name: %s", configs["container_name"])

        parsed_endpoint = urlparse(configs["account_url"])
        log.debug("parsing endpoint")
        log.debug("parsed_endpoint.hostname: %s", parsed_endpoint.hostname)
        log.debug("parsed_endpoint: %s", parsed_endpoint)

        # Handle Azurite endpoint https://github.com/Azure/Azurite vs a real endpoint
        if parsed_endpoint.hostname == "127.0.0.1" or parsed_endpoint.hostname == "localhost":
            account_name = parsed_endpoint.path.split("/")[1]
        else:
            account_name = parsed_endpoint.hostname.split(".")[0]

        log.debug("account_name: %s", account_name)

        options = {
            "container": configs["container_name"],
            "endpoint": configs["account_url"],
            "account_name": account_name,
            "account_key": configs["credential"],
        }

        loader = OpendalReader(
            scheme="azblob",
            file_metadata=lambda_metadata,
            **options,
        )

        documents = loader.load_data()

        file_list = loader.get_document_list()
        log.debug("Number of files: %s", len(file_list))
        persist_path = get_index_dir(space)
        self._save_document_list(file_list, persist_path, self._DOCUMENT_LIST_FILENAME)

        return documents
