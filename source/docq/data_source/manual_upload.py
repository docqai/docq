"""Data source for documents uploaded manually."""

from typing import List

from llama_index import Document, SimpleDirectoryReader

from ..config import DocumentMetadata
from ..domain import ConfigKey, SpaceKey
from ..support.store import get_upload_dir
from .main import SpaceDataSource


class ManualUpload(SpaceDataSource):
    """Space with data from manually uploading documents."""

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("Manual Upload")

    def get_config_keys(self) -> List[ConfigKey]:
        """Get the config keys for manual upload."""
        return []

    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from manual upload."""

        def lambda_metadata(x: str) -> dict:
            return {
                DocumentMetadata.FILE_PATH.value: x,
                DocumentMetadata.SPACE_ID.value: space.id_,
                DocumentMetadata.SPACE_TYPE.value: space.type_.name,
            }

        return SimpleDirectoryReader(get_upload_dir(space), file_metadata=lambda_metadata).load_data()
