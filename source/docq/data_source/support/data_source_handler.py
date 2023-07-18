"""Class to handle listing data sources."""

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

class _Sources(dict):
    __metadata__: dict[str, Any] | None = None
    __data_source_type__: DataSourceType | None = None

    def __init__(self, metadata: dict[str, Any] | None = None) -> None:  # noqa: ANN101
        if metadata is not None:
            self.__metadata__ = metadata
            self.__data_source_type__ = metadata.get("Data Source Type", None)

    def __enter__(self) -> "_Sources": # noqa: ANN101
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None: # noqa: ANN101, ANN001
        self.__metadata__ = None
        self.__data_source_type__ = None

    def __getattr__(self, name: str) -> Any | None: # noqa: ANN101
        if name == "type":
            return self.__data_source_type__

        if self.__metadata__ is not None:
            return self.__metadata__.get(name, None)

        else:
            return None

    def _get_download_url(self) -> str | None: # noqa: ANN101
        from datetime import datetime
        from mimetypes import guess_type

        from streamlit import runtime
        path: str = self.get(DocumentMetadata.FILE_PATH) # type: ignore
        name: str = self.get("file_name") # type: ignore
        if runtime.exists():
            mime_type = guess_type(path)[0] or "application/octet-stream"
            coordinates = str(datetime.now())
            return runtime.get_instance().media_file_mgr.add(
                path_or_data=path,
                mimetype=mime_type,
                coordinates=coordinates,
                file_name=name,
                is_for_static_download=True,
            )

        else:
            return None

    def _get_uri(self) -> str | None: # noqa: ANN101
        if self.__metadata__ is not None:
            return self.get(
                DocumentMetadata.SOURCE_URI, None
                ) if self.get("type") == DataSourceType.MANUAL_UPLOAD else self._get_download_url()

    def get_data(self) -> dict[str, Any] | None: # noqa: ANN101
        """Return the data source metadata."""
        uri = self._get_uri
        page_label = self.get("page_label")
        file_name = self.get("file_name")
        return {
            "uri": uri,
            "page_label": page_label,
            "file_name": file_name,
        }
