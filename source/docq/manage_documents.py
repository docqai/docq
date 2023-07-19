"""Functions to manage documents."""

import logging as log
import os
import shutil
from datetime import datetime
from mimetypes import guess_type
from typing import Any, Dict

from llama_index.schema import NodeWithScore
from streamlit import runtime

from .data_source.main import DocumentMetadata
from .domain import SpaceKey
from .manage_spaces import reindex
from .support.store import get_upload_dir, get_upload_file


def upload(filename: str, content: bytes, space: SpaceKey) -> None:
    """Upload the file to the space."""
    with open(get_upload_file(space, filename), "wb") as f:
        f.write(content)

    reindex(space)


def get_file(filename: str, space: SpaceKey) -> str:
    """Return the path to the file in the space."""
    return get_upload_file(space, filename)


def delete(filename: str, space: SpaceKey) -> None:
    """Delete the file from the space."""
    file = get_upload_file(space, filename)
    os.remove(file)

    reindex(space)


def delete_all(space: SpaceKey) -> None:
    """Delete all files in the space."""
    shutil.rmtree(get_upload_dir(space))

    reindex(space)


def _get_download_link(filename: str, path: str) -> str:
    """Return the download link for the file if runtime exists, otherwise return an empty string."""
    if runtime.exists():
        return runtime.get_instance().media_file_mgr.add(
            path_or_data=path,
            mimetype=guess_type(path)[0] or "application/octet-stream",
            coordinates=str(datetime.now()),
            file_name=filename,
            is_for_static_download=True,
        )

    else:
        return ""


def _parse_metadata(metadata: Dict[str, Any]) -> tuple[Any, Any, Any, Any] | None:
    if not metadata:
        return None
    s_type = metadata.get(DocumentMetadata.DATA_SOURCE_TYPE.value)
    if s_type == "Web Scraper" or s_type ==  "Knowledge Base Scraper":
        website = metadata.get("website")
        page_url = metadata.get("page_url")
        if not website or not page_url:
            return None
        return page_url, None, website, s_type
    uri = metadata.get(DocumentMetadata.SOURCE_URI.value)
    if not uri:
        return None
    page_label = metadata.get("page_label")
    file_name = metadata.get("file_name")
    return uri, page_label, file_name, s_type

def _group_sources(page: str, filename: str, group: dict[str, list[str]] = {}) -> dict[str, list[str]]:  # noqa: B006
    if filename in group:
        group[filename].append(page)
    else:
        group[filename] = [page]
    return group

def format_document_sources(source_nodes: list[NodeWithScore]) -> str:
    """Return the formatted sources with a clickable download link."""
    try:
        delimiter = "\n\n"
        _sources = []
        source_groups: dict[str, list[str]] = {}
        source_uri: dict[str, str] = {}
        source_types: dict[str, str] = {}
        web_sources: dict[str, str] = {}

        for source_node in source_nodes:
            data = _parse_metadata(source_node.node.metadata)
            if data is not None:
                uri, page_label, name, s_type = data
                if not uri or not name or not s_type:
                    continue
                scraper = s_type == "Web Scraper" or s_type ==  "Knowledge Base Scraper"
                if not scraper:
                    source_groups = _group_sources(page_label, name, source_groups)
                    source_uri[name] = uri
                    source_types[name] = s_type
                    continue
                web_sources[name] = uri

        for name, page_labels in source_groups.items():
            uri = source_uri.get(name)
            source_type = source_types.get(name)
            if uri:
                download_url = _get_download_link(name, uri) if source_type == "Manual Upload" else uri
                _sources.append(f"> *File:* [{name}]({download_url})<br> *Pages:* {', '.join(page_labels)}")
        for name, page_url in web_sources.items():
            _sources.append(f"> *Site:* [{name}]({page_url})")
        return delimiter.join(_sources)

    except Exception as e:
        log.exception("Error formatting sources %s", e)
        return "Unable to list sources."
