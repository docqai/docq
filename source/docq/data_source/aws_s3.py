"""Data source backed by AWS S3 (bucket)."""

from typing import List

from llama_index import Document

from ..domain import ConfigKey, SpaceKey
from .main import SpaceDataSource


class AwsS3(SpaceDataSource):
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
