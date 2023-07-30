"""Data source backed by Azure Blob (container)."""

import logging as log
import math
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from azure.storage.blob import ContainerClient, generate_blob_sas
from llama_index import Document, SimpleDirectoryReader
from llama_index.readers.base import BaseReader


class AzStorageBlobReader(BaseReader):
    """General reader for any Azure Storage Blob file or directory.

    Args:
        container_name (str): name of the container for the blob.
        blob (Optional[str]): name of the file to download. If none specified
            this loader will iterate through list of blobs in the container.
        name_starts_with (Optional[str]): filter the list of blobs to download
            to only those whose names begin with the specified string.
        include: (Union[str, List[str], None]): Specifies one or more additional
            datasets to include in the response. Options include: 'snapshots',
            'metadata', 'uncommittedblobs', 'copy', 'deleted',
            'deletedwithversions', 'tags', 'versions', 'immutabilitypolicy',
            'legalhold'.
        file_extractor (Optional[Dict[str, Union[str, BaseReader]]]): A mapping of file
            extension to a BaseReader class that specifies how to convert that file
            to text. See `SimpleDirectoryReader` for more details.
        account_url (str): URI to the storage account, may include SAS token.
        credential (Union[str, Dict[str, str], AzureNamedKeyCredential, AzureSasCredential, TokenCredential, None] = None):
            The credentials with which to authenticate. This is optional if the account URL already has a SAS token.
    """

    def __init__(
        self,
        *args: Optional[Any],
        container_name: str,
        blob: Optional[str] = None,
        name_starts_with: Optional[str] = None,
        include: Optional[Any] = None,
        file_extractor: Optional[Dict[str, Union[str, BaseReader]]] = None,
        account_url: str,
        credential: Optional[Any] = None,
        file_metadata: Optional[Any] = None,
        **kwargs: Optional[Any],
    ) -> None:
        """Initializes Azure Storage Account."""
        super().__init__(*args, **kwargs)

        self.container_name = container_name
        self.blob = blob
        self.name_starts_with = name_starts_with
        self.include = include
        self.file_extractor = file_extractor
        self.account_url = account_url
        self.credential = credential
        self.file_metadata = file_metadata,
        self.extra_metadata = {}

    def _get_blob_sas(self, blob_name: str) -> str:
        """Generate a blob SAS token."""
        return generate_blob_sas(
            account_name=self.account_url.split(".")[0],
            container_name=self.container_name,
            blob_name=blob_name,
            account_key=self.credential,
            permission="r",
            expiry=datetime.utcnow() + timedelta(weeks=4),
        )

    def _load_metadata(self, x: str) -> Dict[str, Any]:
        if self.file_metadata:
            return { **self.file_metadata(x), **self.extra_metadata.get(x) }
        return self.extra_metadata.get(x, {})

    def _set_extra_metadata(self, path: str, key: str) -> None:
        blob_url = self._get_blob_sas(key)
        self.extra_metadata[path] = {
            "blob_url": blob_url,
            "blob_name": key,
        }

    def load_data(self) -> List[Document]:
        """Load file(s) from Azure Storage Blob."""
        container_client = ContainerClient(
            self.account_url, self.container_name, credential=self.credential
        )
        total_download_start_time = time.time()

        with tempfile.TemporaryDirectory() as temp_dir:
            if self.blob:
                extension = Path(self.blob).suffix
                download_file_path = (
                    f"{temp_dir}/{next(tempfile._get_candidate_names())}{extension}"
                )
                log.info("Start download of %s", self.blob)
                start_time = time.time()
                stream = container_client.download_blob(self.blob)
                with open(file=download_file_path, mode="wb") as download_file:
                    stream.readinto(download_file)
                end_time = time.time()
                log.info(
                    f"{self.blob} downloaded in {end_time - start_time} seconds."  # noqa: G004
                )
                self._set_extra_metadata(download_file_path, self.blob)
            else:
                log.info("Listing blobs")
                blobs_list = container_client.list_blobs(
                    self.name_starts_with, self.include
                )
                for obj in blobs_list:
                    extension = Path(obj.name).suffix
                    download_file_path = (
                        f"{temp_dir}/{next(tempfile._get_candidate_names())}{extension}"
                    )
                    log.info(f"Start download of {obj.name}")  # noqa: G004
                    start_time = time.time()
                    stream = container_client.download_blob(obj)
                    with open(file=download_file_path, mode="wb") as download_file:
                        stream.readinto(download_file)
                    end_time = time.time()
                    log.info(
                        f"{obj.name} downloaded in {end_time - start_time} seconds."  # noqa: G004
                    )
                    self._set_extra_metadata(download_file_path, obj.name)

            total_download_end_time = time.time()
            total_elapsed_time = math.ceil(
                total_download_end_time - total_download_start_time
            )
            log.info(
                f"Downloading completed in approximately {total_elapsed_time // 60}min {total_elapsed_time % 60}s."  # noqa: G004
            )
            log.info("Document creation starting")
            loader = SimpleDirectoryReader(temp_dir, file_extractor=self.file_extractor, file_metadata=self._load_metadata)

            return loader.load_data()
