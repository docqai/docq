"""Data source for Docq."""

from abc import ABC, abstractmethod
from typing import List

from llama_index import Document

from ..domain import ConfigKey, SpaceKey


class SpaceDataSource(ABC):
    """Abstract definition of the data source for a space. To be extended by concrete data sources."""

    def __init__(self, name: str) -> None:
        """Initialize the data source."""
        self.name = name

    def get_name(self) -> str:
        """Get the name of the data source."""
        return self.name

    @abstractmethod
    def get_config_keys(self) -> List[ConfigKey]:
        """Get the list of config keys."""
        pass

    @abstractmethod
    def load(self, space: SpaceKey, configs: dict) -> List[Document]:
        """Load the documents from the data source."""
        pass

    @abstractmethod
    def get_document_list(self, space: SpaceKey, configs: dict) -> list[tuple[str, int, int]]:
        """Returns a list of tuples containing the name, creation time, and size (Mb) of each document in the specified space's cnfigured data source.

        Args:
            self (ManualUpload): The ManualUpload object.
            space (SpaceKey): The space to retrieve the document list for.
            configs (dict): A dictionary of configuration options.

        Returns:
            list[tuple[str, int, int]]: A list of tuples containing the name, creation time, and size of each document in the specified space's upload directory.
        """
        pass
