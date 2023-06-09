"""Functions to manage documents."""

import logging as log
import os
import re
import shutil
from datetime import datetime
from mimetypes import guess_type

from llama_index.data_structs.node import NodeWithScore
from llama_index.utils import truncate_text
from streamlit import runtime

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


def _get_download_link(filename: str, space: SpaceKey) -> str:
    """Return the download link for the file if runtime exists, otherwise return an empty string."""
    if runtime.exists():
        file = get_upload_file(space, filename)
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

        for source_node in source_nodes:
            try:
                source = truncate_text(source_node.node.get_text(), 100)
                page_label = re.search(r"(?<=page_label:)(.*)(?=\n)", source)
                file_name = re.search(r"(?<=file_name:)(.*)(?=\n)", source)
                if page_label and file_name:
                    page_label = page_label.group(1).strip()
                    file_name = file_name.group(1).strip()
                    if source_groups.get(file_name):
                        source_groups[file_name].append(page_label)
                    else:
                        source_groups[file_name] = [page_label]
            except Exception as e:
                log.exception("Error formatting source %s", e)
                continue

        for file_name, page_labels in source_groups.items():
            download_url = _get_download_link(file_name, space)
            _sources.append(f"> *File:* [{file_name}]({download_url})<br> *Pages:* {', '.join(page_labels)}")
        return delimiter.join(_sources)

    except Exception as e:
        log.exception("Error formatting sources %s", e)
        return "Unable to list sources."
