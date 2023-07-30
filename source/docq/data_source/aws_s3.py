"""Data source backed by AWS S3 (bucket)."""
import logging as log
from typing import List

from llama_index import Document

from ..domain import ConfigKey, SpaceKey
from .main import DocumentMetadata, SpaceDataSourceFileBased
from .support.s3_reader import S3Reader


class AwsS3(SpaceDataSourceFileBased):
    """Space with data from AWS S3."""

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("AWS S3")

    def get_config_keys(self) -> List[ConfigKey]:
        """Get the config keys for aws s3 bucket."""
        return [
            ConfigKey("bucket", "S3 Bucket Name"),
            ConfigKey("aws_access_id", "AWS Access Key ID", is_secret=True),
            ConfigKey("aws_secret_key", "AWS Secret Access Key", is_secret=True)
        ]

    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from aws s3 bucket."""
        def lambda_apend_metadata(x: str) -> dict:
            return {
                DocumentMetadata.SPACE_ID.name: space.id_,
                DocumentMetadata.SPACE_TYPE.name: space.type_.name,
                DocumentMetadata.DATA_SOURCE_NAME.name: self.get_name(),
                DocumentMetadata.DATA_SOURCE_TYPE.name: self.__class__.__base__.__name__,
                "debug_key": x,
            }
        loader = S3Reader(
            bucket=configs["bucket"],
            aws_access_id=configs["aws_access_id"],
            aws_access_secret=configs["aws_secret_key"],
            file_metadata=lambda_apend_metadata,
        )

        return loader.load_data()

    def get_document_list(self, space: SpaceKey, configs: dict) -> list[tuple[str, int, int]]:
        """Returns a list of tuples containing the name, creation time, and size (Mb) of each document in the specified space's cnfigured data source.

        Args:
            space (SpaceKey): The space to retrieve the document list for.
            configs (dict): A dictionary of configuration options.

        Returns:
            list[tuple[str, int, int]]: A list of tuples containing the name, creation time, and size of each document in the specified space's upload directory.
        """
        import boto3
        from botocore.exceptions import ClientError
        try:
            session = boto3.Session(
                aws_access_key_id=configs["aws_access_id"],
                aws_secret_access_key=configs["aws_secret_key"],
            )
            bucket = session.resource("s3").Bucket(configs["bucket"])
            return [(obj.key, obj.last_modified.timestamp(), obj.size / 1e6) for obj in bucket.objects.all()]
        except ClientError as e:
            log.error("Failed to retrieve document list from S3 bucket: %s", e)
