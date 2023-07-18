"""Functions to manage documents."""

import logging as log
import os
import shutil
from datetime import datetime
from mimetypes import guess_type

from llama_index.schema import NodeWithScore
from streamlit import runtime

from .data_source.support.data_source_handler import DataSourceType, Source
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
        file = path
        mime_type = guess_type(file)[0] or "application/octet-stream"
        coordinates = str(datetime.now())
        return runtime.get_instance().media_file_mgr.add(
            path_or_data=file,
            mimetype=mime_type,
            coordinates=coordinates,
            file_name=filename,
            is_for_static_download=True,
        )

    else:
        return ""


def format_document_sources(source_nodes: list[NodeWithScore], space: SpaceKey) -> str:
    """Return the formatted sources with a clickable download link."""
    try:
        delimiter = "\n\n"
        _sources = []
        source_groups: dict[str, list[str]] = {}
        source_uri: dict[str, str] = {}
        source_types: dict[str, str] = {}

        for source_node in source_nodes:
            with Source(source_node.node.metadata) as source:
                data = source.data
                if data is not None:
                    uri, page_label, file_name, s_type = data.values()
                    manual_upload = s_type == DataSourceType.MANUAL_UPLOAD.value
                    if manual_upload and (not uri or not page_label or not file_name):
                        continue
                    if not manual_upload and (not uri or not file_name or not s_type):
                        continue
                    source_groups = source.group_sources(page_label, file_name, source_groups)
                    source_uri = source.group_source_uri(uri, file_name, source_uri)
                    source_types = source.group_source_uri(s_type, file_name, source_types)

        for file_name, page_labels in source_groups.items():
            uri = source_uri.get(file_name)
            source_type = source_types.get(file_name)
            if uri:
                download_url = _get_download_link(file_name, uri) if source_type == DataSourceType.MANUAL_UPLOAD.value else uri
                _sources.append(f"> *File:* [{file_name}]({download_url})<br> *Pages:* {', '.join(page_labels)}")
        return delimiter.join(_sources)

    except Exception as e:
        log.exception("Error formatting sources %s", e)
        return "Unable to list sources."
