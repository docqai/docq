"""Source formatter module."""
import logging as log
import os
import unicodedata
from abc import ABC, abstractmethod
from datetime import datetime
from mimetypes import guess_type
from typing import Any, DefaultDict, Self

from llama_index.schema import NodeWithScore
from streamlit import runtime

from ..data_source.main import DocumentMetadata


class Source(ABC):
    """Source base class."""
    def __init__(self: Self, metadata: dict) -> None:
        """Initialize the source object."""
        self._metadata = metadata

    @property
    @abstractmethod
    def is_valid(self: Self) -> bool:
        """Return True if the source is valid, False otherwise."""
        pass

    @property
    @abstractmethod
    def name(self: Self) -> str:
        """File name or website name."""
        pass

    @property
    @abstractmethod
    def source_uri(self: Self) -> str:
        """Download link or website url."""
        pass

    @abstractmethod
    def group_info(self: Self) -> tuple[str, Any]:
        """Group info for the source."""
        pass

    def _get_download_link(self: Self, filename: str, path: str) -> str:
        """Return the download link for the file if runtime exists, otherwise return an empty string."""
        if runtime.exists() and os.path.isfile(path):
            return runtime.get_instance().media_file_mgr.add(
                path_or_data=path,
                mimetype=guess_type(path)[0] or "application/octet-stream",
                coordinates=str(datetime.now()),
                file_name=filename,
                is_for_static_download=True,
            )

        else:
            return "#"

    def _remove_ascii_control_characters(self: Self, text: str) -> str:
        """Remove ascii control characters from the text."""
        return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")

class FileSource(Source):
    """File based source formatter."""
    def __init__(self: Self, metadata: dict) -> None:
        """Initialize the file source object."""
        super().__init__(metadata)
        self._name = self._metadata.get("file_name")
        self._page_label = self._metadata.get("page_label")
        self._uri = self._metadata.get(str(DocumentMetadata.SOURCE_URI.name).lower())

    @property
    def is_valid(self: Self) -> bool:
        """Return True if the source is valid, False otherwise."""
        return bool(self._name and self._uri)

    @property
    def name(self: Self) -> str:
        """File name."""
        return self._name

    @property
    def source_uri(self: Self) -> str:
        """File download link."""
        return self._get_download_link(self._name, self._uri)

    def group_info(self: Self) -> tuple[str, Any]:
        """Group info for the source."""
        return self._name, self._page_label

class WebSource(Source):
    """Web based source formatter."""
    def __init__(self: Self, metadata: dict) -> None:
        """Initialize the web source object."""
        super().__init__(metadata)
        self._name = self._remove_ascii_control_characters(metadata.get("source_website"))
        self._page_title = self._remove_ascii_control_characters(metadata.get("page_title"))
        self._page_url = self._metadata.get(str(DocumentMetadata.SOURCE_URI.name).lower())

    @property
    def is_valid(self: Self) -> bool:
        """Check if the source is valid."""
        return bool(self._name and self._page_url)

    @property
    def name(self: Self) -> str:
        """Website name."""
        return self._name

    @property
    def source_uri(self: Self) -> str:
        """Link to the website."""
        return self._page_url

    def group_info(self: Self) -> tuple[str, Any]:
        """Group info for the source."""
        return self._name, (self._page_title, self._page_url)

def parse_source(metadata: dict) -> Source:
    """Parse the source from the metadata."""
    s_type = metadata.get(str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower())
    if s_type == 'SpaceDataSourceWebBased':
        return WebSource(metadata)
    return FileSource(metadata)

def format_document_sources(source_nodes: list[NodeWithScore]) -> str:
    """Format the document sources."""
    try:
        file_sources = DefaultDict(list)
        web_sources = DefaultDict(list)
        site_delimiter = "\n>- "
        file_delimiter = "\n\n"

        for source_node in source_nodes:
            source = parse_source(source_node.node.metadata)
            if source.is_valid:
                name, info = source.group_info()
                if isinstance(source, WebSource):
                    web_sources[name].append(info)
                else:
                    file_sources[name].append(info)

        _sources = []
        for name, pages in file_sources.items():
            _sources.append(f"> *File:* [{name}]({source.source_uri})<br> *Pages:* {', '.join(pages)}")
        for site, pages in web_sources.items():
            page_str = "\n>- ".join([f"[{title}]({page})" for title, page in pages])
            _sources.append(f"\n> ###### {site} {site_delimiter if page_str else ''} {page_str}")

        fmt_sources = f'\n##### Source{"s" if len(_sources) > 1 else ""}:\n {file_delimiter.join(_sources)}'
        return fmt_sources if bool(_sources) else ""
    except Exception as e:
        log.exception("Error formatting sources %s", e)
        return "Unable to list sources."
