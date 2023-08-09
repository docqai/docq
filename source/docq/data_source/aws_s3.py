"""Data source backed by AWS S3 (bucket)."""

from typing import List

from llama_index import Document

from ..domain import ConfigKey, SpaceKey
from .main import SpaceDataSourceFileBased
from .support.utils import DocumentListItem


class AwsS3(SpaceDataSourceFileBased):
    """Space with data from AWS S3."""

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("AWS S3")

    def get_config_keys(self) -> List[ConfigKey]:
        """Get the config keys for aws s3 bucket."""
        return [
            ConfigKey("bucket_url", "S3 Bucket URL"),
        ]

    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from aws s3 bucket."""
        # TODO: use aws s3 bucket to load the documents
        pass

    def get_document_list(self, space: SpaceKey, configs: dict) -> List[DocumentListItem]:
        """Returns a list of tuples containing the name, creation time, and size (Mb) of each document in the specified space's cnfigured data source.

        Args:
            space (SpaceKey): The space to retrieve the document list for.
            configs (dict): A dictionary of configuration options.

        Returns:
            List[DocumentListItem]: A list of tuples containing the name, creation time, and size of each document in the specified space's upload directory.
        """
        # TODO: use aws s3 bucket to get the document list
        pass
