"""Data source for Docq."""

import json
import logging as log
import os
from abc import ABC, abstractmethod
from dataclasses import asdict
from enum import Enum
from typing import List, Self

from llama_index import Document
from opentelemetry import trace

from ..domain import ConfigKey, DocumentListItem, SpaceKey
from ..support.store import get_index_dir


class DocumentMetadata(Enum):
    """Document metadata."""

    FILE_PATH = "File Path"
    SPACE_ID = "Space ID"
    SPACE_TYPE = "Space Type"
    DATA_SOURCE_TYPE = "Data Source Type"
    DATA_SOURCE_NAME = "Data Source Name"
    INDEXED_ON = "Indexed Timestamp"
    SOURCE_URI = "Source URI"


trace = trace.get_tracer("docq.api.data_source")


class SpaceDataSource(ABC):
    """Abstract definition of the data source for a space. To be extended by concrete data sources."""

    def __init__(self: Self, name: str) -> None:
        """Initialize the data source."""
        self.name = name

    def get_name(self: Self) -> str:
        """Get the name of the data source."""
        return self.name

    @abstractmethod
    def get_config_keys(self) -> List[ConfigKey]:
        """Get the list of config keys."""
        pass

    @abstractmethod
    @trace.start_as_current_span("SpaceDataSource.load")
    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from the data source."""
        pass

    @abstractmethod
    @trace.start_as_current_span("SpaceDataSource.get_document_list")
    def get_document_list(self, space: SpaceKey, configs: dict) -> List[DocumentListItem]:
        """Returns a list of tuples containing the name, creation time, and size (Mb) of each document in the specified space's cnfigured data source.

        Args:
            space (SpaceKey): The space to retrieve the document list for.
            configs (dict): A dictionary of configuration options.

        Returns:
            List[DocumentListItem]: A list of tuples containing the name, creation time, and size of each document in the specified space's upload directory.
        """
        pass


class SpaceDataSourceFileBased(SpaceDataSource):
    """Abstract definition of a file-based data source for a space. To be extended by concrete data sources."""

    _DOCUMENT_LIST_FILENAME = "document_list.json"

    def get_document_list(self, space: SpaceKey, configs: dict) -> List[DocumentListItem]:
        """Get the list of documents."""
        persist_path = get_index_dir(space)
        return self._load_document_list(persist_path, self._DOCUMENT_LIST_FILENAME)

    @trace.start_as_current_span("SpaceDataSourceFileBased._save_document_list")
    def _save_document_list(self, document_list: List[DocumentListItem], persist_path: str, filename: str) -> None:
        path = os.path.join(persist_path, filename)
        try:
            data = [asdict(item) for item in document_list]
            with open(path, "w") as f:
                # the field names of the namedtuple are lost when we serialize to json.
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                )
            log.debug("Saved space index document list to '%s'", path)
        except Exception as e:
            log.error("Failed to save space index document list to '%s': %s", path, e, stack_info=True)

    @trace.start_as_current_span("SpaceDataSourceFileBased._load_document_list")
    def _load_document_list(self, persist_path: str, filename: str) -> List[DocumentListItem]:
        path = os.path.join(persist_path, filename)
        with open(path, "r") as f:
            data = json.load(f)
            # convert back to a namedtuple so we have field names.
            document_list = [DocumentListItem(**item) for item in data]
            return document_list

    @trace.start_as_current_span("SpaceDataSourceFileBased._add_exclude_metadata_keys")
    def _add_exclude_metadata_keys(
        self, documents: List[Document], embed_keys: List[str], llm_keys: List[str]
    ) -> List[Document]:
        """Exclude metadata keys from embedding and LLM."""
        if documents is None:
            raise ValueError("`documents` cannot be None")
        doc_count = len(documents)
        for i in range(doc_count):
            documents[i].excluded_embed_metadata_keys = embed_keys
            documents[i].excluded_llm_metadata_keys = llm_keys
        return documents


class SpaceDataSourceWebBased(SpaceDataSourceFileBased):
    """Abstract definition of a web-based data source for a space. To be extended by concrete data sources."""
