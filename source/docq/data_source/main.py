"""Data source for Docq."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from llama_index import Document

from ..domain import ConfigKey, SpaceKey


class DocumentMetadata(Enum):
    """Document metadata."""

    FILE_PATH = "File Path"
    SPACE_ID = "Space ID"
    SPACE_TYPE = "Space Type"
    INDEXED_ON = "Indexed On"
    SOURCE_URI = "Source URI"


class SpaceDataSource(ABC):
    """Abstract definition of the data source for a space. To be extended by concrete data sources."""

    def __init__(self, name: str, _type: str) -> None:
        """Initialize the data source."""
        self.name = name
        self._type = _type

    def get_name(self) -> str:
        """Get the name of the data source."""
        return self.name

    def get_type(self) -> str:
        """Get the type of this data source."""
        return self.type

    @abstractmethod
    def get_config_keys(self) -> List[ConfigKey]:
        """Get the list of config keys."""
        pass

    @abstractmethod
    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from the data source."""
        pass


class SpaceDataSourceFileBased(SpaceDataSource):
    """Abstract definition of a file-based data source for a space. To be extended by concrete data sources."""

    @abstractmethod
    def get_document_list(self, space: SpaceKey, configs: dict) -> list[tuple[str, int, int]]:
        """Returns a list of tuples containing the name, creation time, and size (Mb) of each document in the specified space's cnfigured data source.

        Args:
            space (SpaceKey): The space to retrieve the document list for.
            configs (dict): A dictionary of configuration options.

        Returns:
            list[tuple[str, int, int]]: A list of tuples containing the name, creation time, and size of each document in the specified space's upload directory.
        """
        pass


class SpaceDataSourceWebBased(SpaceDataSource):
    """Abstract definition of a file-based data source for a space. To be extended by concrete data sources."""

    @abstractmethod
    def get_document_list(self, space: SpaceKey, configs: dict, persist_path: str) -> list[tuple[str, int, int]]:
        """Returns a list of tuples containing the name, creation time, and size (Mb) of each document in the specified space's cnfigured data source.

        Args:
            space (SpaceKey): The space to retrieve the document list for.
            configs (dict): A dictionary of configuration options.
            persist_path (str): The path to persist the downloaded document list.

        Returns:
            list[tuple[str, int, int]]: A list of tuples containing the name, creation time, and size of each document in the specified space's upload directory.
        """
        pass
