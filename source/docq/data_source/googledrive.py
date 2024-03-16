"""Google drive datasource."""
import json
import logging as log
from datetime import datetime
from typing import Any, List, Self

from llama_index.core.schema import Document

from .. import services
from ..domain import ConfigKey, SpaceKey
from ..support.store import get_index_dir
from .main import DocumentMetadata, FileStorageServiceKeys, SpaceDataSourceFileBased
from .support.opendal_reader.base import GoogleDriveReader, OpendalReader


class GDrive(SpaceDataSourceFileBased):
    """Space data source for Google Drive."""

    def __init__(self: Self) -> None:
        """Initialize the data source."""
        super().__init__("Google Drive")
        self.credential = f"{FileStorageServiceKeys.GOOGLE_DRIVE.name}-credential"
        self.root_path = f"{FileStorageServiceKeys.GOOGLE_DRIVE.name}-root_path"

    def list_folders(self: Self, configs: Any, state: dict) -> tuple[list, bool]:
        """List google drive folders."""
        __creds = configs.get(self.credential) if configs else state.get(self.credential, None)
        creds = services.google_drive.validate_credentials(__creds)

        return (services.google_drive.list_folders(creds), False) if creds else ([], False)

    @property
    def disabled(self: Self) -> bool:
        """Disable the data source."""
        return not services.google_drive.api_enabled()

    def get_config_keys(self: Self) -> List[ConfigKey]:
        """Get the config keys for google drive."""
        return [
            ConfigKey(
                self.credential,
                "Credential",
                is_secret=True,
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-google-drive",
                options={
                    "type": "credential",
                    "handler": services.google_drive.get_auth_url,
                    "btn_label": "Sign in with Google",
                }
            ),
            ConfigKey(
                self.root_path,
                "Select a folder",
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-google-drive",
                options={
                    "type": "root_path",
                    "handler": self.list_folders,
                    "format_function": lambda x: x['name'],
                }
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

        root_path = configs[self.root_path]

        options = {
            "root": root_path["name"],
            "access_token": json.dumps(configs[self.credential]),
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
                access_token=configs[self.credential],
                selected_folder_id=root_path["id"]
            )

        documents = loader.load_data()
        file_list = loader.get_document_list()
        log.debug("Loaded %s documents from google drive", len(file_list))
        persist_path = get_index_dir(space)
        self._save_document_list(file_list, persist_path, self._DOCUMENT_LIST_FILENAME)
        return documents
