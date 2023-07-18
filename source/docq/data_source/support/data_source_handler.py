"""Class to handle listing data sources."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..main import DocumentMetadata


class DataSourceType(Enum):
    """Data source types."""

    MANUAL_UPLOAD = "Manual Upload"
    AZURE_BLOB = "Azure Blob"
    AWS_S3 = "AWS S3"
    WEB_SCRAPER = "Web Scraper"
    KNOWLEDGE_BASE_SCRAPER = "Knowledge Base Scraper"

# Type declarations
Source_Groups = dict[str, list[str]]
Source_Uri = dict[str, str]
Metadata = dict[str, Any] | None

@dataclass
class Source:
    """Handle the various respone sources."""
    __metadata__: Metadata = None
    __data_source_type__: DataSourceType | None = None

    def __init__(self: "Source", metadata: Metadata = None) -> None:
        """Setup metadata."""
        if metadata is not None:
            self.__metadata__ = metadata
            self.__data_source_type__ = metadata.get(DocumentMetadata.DATA_SOURCE_TYPE.value, None)

    def __enter__(self: "Source") -> "Source":
        """Context manager."""
        return self

    @property
    def data(self: "Source") -> Metadata:
        """Class property containing formatted source node data.

        Returns:
            dict[str, Any] | None: The formatted source node data.
            uri (str): The source uri.
            page_label (str): The page label.
            file_name (str): The file name.
            type (DataSourceType): The data source type.
        """
        return self._get_data()

    def _get_data(self: "Source") -> Metadata:
        """Return the data source metadata."""
        if self.__metadata__ is not None:
            uri = self.__metadata__.get(DocumentMetadata.SOURCE_URI.value, None)
            page_label = self.__metadata__.get("page_label")
            file_name = self.__metadata__.get("file_name")
            return {
                "uri": uri,
                "page_label": page_label,
                "file_name": file_name,
                "type": self.__data_source_type__
            }
        return None

    def group_sources(self: "Source", page:str, filename: str, source_group: Source_Groups = {}) -> Source_Groups: # noqa: B006
        """Group similar sources together.

        Args:
            page (str): The page label.
            filename (str): The file name.
            source_group (Source_Groups, optional): The source group. Defaults to {}.

        Returns:
            Source_Groups: The source group.
        """
        if source_group.get(filename):
            source_group[filename].append(page)
        else:
            source_group[filename] = [page]

        return source_group

    def group_source_uri(self: "Source", uri: str, filename: str,  source_group: Source_Uri = {}) -> Source_Uri: # noqa: B006
        """Group similar source uri's together.

        Args:
            filename (str): The file name.
            uri (str): The uri.
            source_group (Source_Uri, optional): The source group. Defaults to {}.

        Returns:
            Source_Uri: The source group.
        """
        source_group[filename] = uri
        return source_group

    def __exit__(self: "Source", exc_type: Any, exc_value: Any, traceback: Any) -> None:  # noqa: ANN401
        """Cleanup."""
        self.__metadata__ = None
        self.__data_source_type__ = None
