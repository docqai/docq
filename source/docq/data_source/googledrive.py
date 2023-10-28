"""Google drive datasource test."""
import json
import logging as log

# import tempfile
from datetime import datetime
from typing import List, Self

from llama_index import Document

from ..config import ConfigKeyHandlers, ConfigKeyOptions
from ..domain import ConfigKey, SpaceKey
from ..support.store import get_index_dir
from .main import DocumentMetadata, SpaceDataSourceFileBased
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
                ConfigKeyOptions.GET_GDRIVE_OPTIONS.name,
                "Select a folder",
                input_element="selectbox",
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-google-drive",
            ),
            ConfigKey(
                ConfigKeyHandlers.GET_GDRIVE_CREDENTIAL.name,
                "Credential",
                is_hidden=True,
                input_element="none"
            )
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

        drive_options = configs[ConfigKeyOptions.GET_GDRIVE_OPTIONS.name]

        options = {
            "root": drive_options["name"],
            "access_token": json.dumps(configs[ConfigKeyHandlers.GET_GDRIVE_CREDENTIAL.name]),
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
                root=drive_options["name"],
                access_token=configs[ConfigKeyHandlers.GET_GDRIVE_CREDENTIAL.name],
                selected_folder_id=drive_options["id"]
            )

        documents = loader.load_data()
        file_list = loader.get_document_list()
        log.debug("Loaded %s documents from google drive", len(file_list))
        persist_path = get_index_dir(space)
        self._save_document_list(file_list, persist_path, self._DOCUMENT_LIST_FILENAME)
        return documents
