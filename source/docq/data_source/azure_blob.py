"""Data source backed by Azure Blob (container)."""

import logging as log
from datetime import datetime
from typing import Any, Dict, List

from azure.core.exceptions import ClientAuthenticationError
from llama_index import Document

from ..domain import ConfigKey, SpaceKey
from .main import DocumentMetadata, SpaceDataSourceFileBased
from .support.az_reader import AzStorageBlobReader


class AzureBlob(SpaceDataSourceFileBased):
    """Space with data from Azure Blob."""

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

        # str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower(): self.__class__.__base_.__name__,
        def lambda_apend_metadata(x: str) -> Dict:
           return {
                    DocumentMetadata.SPACE_ID.name: space.id_,
                    DocumentMetadata.SPACE_TYPE.name: space.type_.name,
                    DocumentMetadata.DATA_SOURCE_NAME.name: self.get_name(),
                    DocumentMetadata.DATA_SOURCE_TYPE.name: self.__class__.__base__.__name__,
                    "debug_key": x,
                }

        # AzStorageBlobReader = download_loader("AzStorageBlobReader")  # noqa: N806
        log.debug("account_url: %s", configs["account_url"])
        log.debug("container_name: %s", configs["container_name"])
        loader = AzStorageBlobReader(
            container_name=configs["container_name"],
            account_url=configs["account_url"],
            credential=configs["credential"],
            metadata_template=lambda_apend_metadata,
        )

        documents = loader.load_data()

        return documents

    def get_document_list(self, space: SpaceKey, configs: dict) -> list[tuple[str, int, int]]:
        """Get the list of documents."""
        from azure.storage.blob import ContainerClient

        try:
            container_client = ContainerClient(configs["account_url"], configs["container_name"], configs["credential"])
            blobs_list = container_client.list_blobs()
            return list(map(lambda b: (b.name, datetime.timestamp(b.last_modified), b.size), blobs_list))
        except ClientAuthenticationError as e:
            log.error("Error - get_document_list(): authenticating to Azure Blob: %s", e)
            raise Exception(
                "Ooops! something went wrong authenticating to Azure storage. Please check your datasource credentials are correct and try again. If using a SAS Token make sure it hasn't expired.",
            ) from e
        except PermissionError as e:
            log.error("Error - get_document_list(): checking permissions on Azure Blob: %s", e)
            raise Exception(
                "Ooops! something went wrong checking permissions on Azure storage. Please check your datasource credentials are correct and try again. Make sure you have 'Read' and 'List' permission for the Blob container."
            ) from e
        except Exception as e:
            log.error("Error - get_document_list(): %s", e)
            raise Exception("Ooops! something that we didn't anticipate went wrong, sorry.") from e
