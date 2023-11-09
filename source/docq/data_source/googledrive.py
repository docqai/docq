"""Google drive datasource."""
import json
import logging as log
from datetime import datetime
from typing import List, Self

from llama_index import Document

from ..domain import ConfigKey, SpaceKey
from ..support.store import get_index_dir
from .main import DocumentMetadata, FileStorageServiceKeys, SpaceDataSourceFileBased
from .support.opendal_reader.base import GoogleDriveReader, OpendalReader


class GDrive(SpaceDataSourceFileBased):
    """Space data source for Google Drive."""

    def __init__(self: Self) -> None:
        """Initialize the data source."""
        super().__init__("Google Drive")

    def get_config_keys(self: Self) -> List[ConfigKey]:
        """Get the config keys for google drive."""
        return [
            ConfigKey(
                f"{FileStorageServiceKeys.GOOGLE_DRIVE}-credential",
                "Credential",
                is_secret=True,
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-google-drive",
            ),
            ConfigKey(
                f"{FileStorageServiceKeys.GOOGLE_DRIVE}-root_path",
                "Select a folder",
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-google-drive",
            ),
        ]

    def load(self: Self, space: SpaceKey, configs: dict) -> list[Document] | None:
        """Load the documents from google drive."""

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

        root_path = configs[f"{FileStorageServiceKeys.GOOGLE_DRIVE}-root_path"]

        options = {
            "root": root_path["name"],
            "access_token": json.dumps(configs[f"{FileStorageServiceKeys.GOOGLE_DRIVE}-credential"]),
        }

        try:
            loader = OpendalReader(
                scheme="gdrive",
                file_metadata=lambda_metadata,
                **options,
            )
        except Exception as e:
            log.error("Failed to load google drive with opendal reader: %s", e)
            loader = GoogleDriveReader(
                file_metadata=lambda_metadata,
                root=root_path["name"],
                access_token=configs[f"{FileStorageServiceKeys.GOOGLE_DRIVE}-credential"],
                selected_folder_id=root_path["id"]
            )

        documents = loader.load_data()
        file_list = loader.get_document_list()
        log.debug("Loaded %s documents from google drive", len(file_list))
        persist_path = get_index_dir(space)
        self._save_document_list(file_list, persist_path, self._DOCUMENT_LIST_FILENAME)
        return documents
