"""Data source for documents uploaded manually."""

import logging
import os
from datetime import datetime
from typing import List

from llama_index import Document, SimpleDirectoryReader
from opentelemetry import trace

from ..domain import ConfigKey, DocumentListItem, SpaceKey
from ..support.store import get_upload_dir
from .main import DocumentMetadata, SpaceDataSourceFileBased


class ManualUpload(SpaceDataSourceFileBased):
    """Space with data from manually uploading documents."""

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("Manual Upload")

    def get_config_keys(self) -> List[ConfigKey]:
        """Get the config keys for manual upload."""
        return []

    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from manual upload."""

        # Keep filename as `doc_id` plus space info
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

        _documents = SimpleDirectoryReader(get_upload_dir(space), file_metadata=lambda_metadata).load_data()

        pdfreader_metadata_keys = ["page_label", "file_name"]
        exclude_embed_metadata_keys_ = [
            str(DocumentMetadata.FILE_PATH.name).lower(),
            str(DocumentMetadata.SPACE_ID.name).lower(),
            str(DocumentMetadata.SPACE_TYPE.name).lower(),
            str(DocumentMetadata.DATA_SOURCE_NAME.name).lower(),
            str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower(),
            str(DocumentMetadata.SOURCE_URI.name).lower(),
            str(DocumentMetadata.INDEXED_ON.name).lower(),
        ]
        exclude_embed_metadata_keys_.extend(pdfreader_metadata_keys)

        excluded_llm_metadata_keys_ = [
            str(DocumentMetadata.FILE_PATH.name).lower(),
            str(DocumentMetadata.SPACE_ID.name).lower(),
            str(DocumentMetadata.SPACE_TYPE.name).lower(),
            str(DocumentMetadata.DATA_SOURCE_NAME.name).lower(),
            str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower(),
            str(DocumentMetadata.INDEXED_ON.name).lower(),
        ]
        # logging.debug("exclude_embed_metadata_keys_: %s", exclude_embed_metadata_keys_)
        # logging.debug("excluded_llm_metadata_keys_: %s", excluded_llm_metadata_keys_)
        # exclude all meta-metadata from embedding to improve retrieval. The LLM needs some for referencing.
        # for i in range(len(documents_)):
        #     documents_[i].excluded_embed_metadata_keys = exclude_embed_metadata_keys_
        #     documents_[i].excluded_llm_metadata_keys = excluded_llm_metadata_keys_

        return self._add_exclude_metadata_keys(_documents, exclude_embed_metadata_keys_, excluded_llm_metadata_keys_)

    def get_document_list(self, space: SpaceKey, configs: dict) -> List[DocumentListItem]:
        """Returns a list of tuples containing the name, creation time, and size (Mb) of each document in the specified space's configured data source.

        Args:
            self (ManualUpload): The ManualUpload object.
            space (SpaceKey): The space to retrieve the document list for.
            configs (dict): A dictionary of configuration options.

        Returns:
            List[DocumentListItem]: A list of tuples containing the name, creation time, and size of each document in the specified space's upload directory.
        """
        return list(
            map(
                lambda f: DocumentListItem(f.name, int(f.stat().st_ctime), f.stat().st_size),
                os.scandir(get_upload_dir(space)),
            )
        )
