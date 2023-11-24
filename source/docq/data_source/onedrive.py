"""Onedrive drive datasource module."""
import logging as log
from datetime import datetime
from typing import Any, List, Self

from llama_index import Document

from .. import services
from ..domain import ConfigKey, SpaceKey
from ..support.store import get_index_dir
from .main import DocumentMetadata, FileStorageServiceKeys, SpaceDataSourceFileBased
from .support.opendal_reader.base import OneDriveReader, OpendalReader


class OneDrive(SpaceDataSourceFileBased):
    """Space data source for OneDrive."""

    def __init__(self: Self) -> None:
        """Initialize the data source."""
        super().__init__("OneDrive")
        self.credential = f"{FileStorageServiceKeys.ONEDRIVE.name}-credential"
        self.root_path = f"{FileStorageServiceKeys.ONEDRIVE.name}-root_path"

    def list_folders(self: Self, configs: Any, state: dict) -> tuple[list, bool]:
        """List onedrive drive folders."""
        __token = configs.get(self.credential) if configs else state.get(self.credential, None)
        token = services.ms_onedrive.validate_credentials(__token)

        return (services.ms_onedrive.list_folders(token), False) if token else ([], False)

    @property
    def disabled(self: Self) -> bool:
        """Disable the data source."""
        return not services.ms_onedrive.api_enabled()

    def get_config_keys(self: Self) -> List[ConfigKey]:
        """Get the config keys for onedrive."""
        return [
            ConfigKey(
                self.credential,
                "Credential",
                is_secret=True,
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-onedrive",
                options={
                    "type": "credential",
                    "handler": services.ms_onedrive.get_auth_url,
                    "btn_label": "Signin with Microsoft",
                }
            ),
            ConfigKey(
                self.root_path,
                "Select a folder",
                ref_link="https://docqai.github.io/docq/user-guide/config-spaces/#data-source-onedrive",
                options={
                    "type": "root_path",
                    "handler": self.list_folders,
                    "format_function": lambda x: x["name"],
                }
            ),
        ]

    def load(self: Self, space: SpaceKey, configs: dict) -> list[Document] | None:
        """Load the documents from onedrive."""

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
            "access_token": configs[self.credential].to_json,
        }

        try:
            loader = OpendalReader(
                scheme="onedrive",
                file_metadata=lambda_metadata,
                **options,
            )
        except Exception as e:
            log.error("Failed to load onedrive with opendal reader: %s", e)
            loader = OneDriveReader(
                file_metadata=lambda_metadata,
                root=root_path["name"],
                access_token=configs[self.credential],
                selected_folder_id=root_path["id"]
            )

        documents = loader.load_data()
        file_list = loader.get_document_list()
        log.debug("Loaded %s documents from onedrive", len(file_list))
        persist_path = get_index_dir(space)
        self._save_document_list(file_list, persist_path, self._DOCUMENT_LIST_FILENAME)
        return documents
