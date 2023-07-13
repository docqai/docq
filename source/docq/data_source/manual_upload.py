"""Data source for documents uploaded manually."""

import os
from datetime import datetime
from typing import List

from llama_index import Document, SimpleDirectoryReader

from ..domain import ConfigKey, SpaceKey
from ..support.store import get_upload_dir
from .main import DocumentMetadata, SpaceDataSourceFileBased


class ManualUpload(SpaceDataSourceFileBased):
    """Space with data from manually uploading documents."""

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("Manual Upload", "MANUAL_UPLOAD")

    def get_config_keys(self) -> List[ConfigKey]:
        """Get the config keys for manual upload."""
        return []

    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from manual upload."""

        # Keep filename as `doc_id` plus space info
        def lambda_metadata(x: str) -> dict:
            return {
                DocumentMetadata.FILE_PATH.name: x,
                DocumentMetadata.SPACE_ID.name: space.id_,
                DocumentMetadata.SPACE_TYPE.name: space.type_.name,
                DocumentMetadata.SOURCE_URI.name: x,
                DocumentMetadata.INDEXED_ON.name: datetime.timestamp(datetime.now().utcnow()),
            }

        return SimpleDirectoryReader(get_upload_dir(space), file_metadata=lambda_metadata).load_data()

    def get_document_list(self, space: SpaceKey, configs: dict) -> list[tuple[str, int, int]]:
        """Returns a list of tuples containing the name, creation time, and size (Mb) of each document in the specified space's cnfigured data source.

        Args:
            self (ManualUpload): The ManualUpload object.
            space (SpaceKey): The space to retrieve the document list for.
            configs (dict): A dictionary of configuration options.

        Returns:
            list[tuple[str, int, int]]: A list of tuples containing the name, creation time, and size of each document in the specified space's upload directory.
        """
        return list(
            map(
                lambda f: (f.name, f.stat().st_ctime, f.stat().st_size),
                os.scandir(get_upload_dir(space)),
            )
        )
