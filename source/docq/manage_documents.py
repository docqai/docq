"""Functions to manage documents."""

import os
import shutil

from .domain import SpaceKey
from .support.llm import reindex
from .support.store import get_upload_dir, get_upload_file
from streamlit import runtime
from mimetypes import guess_type
from datetime import datetime
import re
from llama_index.utils import truncate_text
import logging as log
from llama_index.data_structs.node import NodeWithScore


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


def list_all(space: SpaceKey) -> list[tuple[str, int, int]]:
    """Return a list of tuples containing the filename, creation time, and size of each file in the space."""
    return list(map(lambda f: (f.name, f.stat().st_ctime, f.stat().st_size), os.scandir(get_upload_dir(space))))


def _get_download_link(filename: str, space: SpaceKey) -> str:
    """Return the download link for the file if runtime exists, otherwise return an empty string."""
    if runtime.exists():
        file = get_upload_file(space, filename)
        return runtime.get_instance().media_file_mgr.add(
            path_or_data=file,
            mimetype=guess_type(file)[0],
            coordinates=datetime.now(),
            file_name=filename,
            is_for_static_download=True,
        )

    else:
        return ""


def format_document_sources(source_nodes: NodeWithScore, space: SpaceKey) -> str:
    """Return the formatted sources with a clickable download link."""
    delimitter = "\n\n"
    _sources = []

    for source_node in source_nodes:
        try:
            source = truncate_text(source_node.node.get_text(), 100)
            page_label = re.search(r"(?<=page_label:)(.*)(?=\n)", source)
            file_name = re.search(r"(?<=file_name:)(.*)(?=\n)", source)
            if page_label and file_name:
                page_label = page_label.group(1).strip()
                file_name = file_name.group(1).strip()
                download_url = _get_download_link(file_name, space)
                id = source_node.doc_id or None
                _sources.append(f"> Source(Doc id: {id})<br> *File name:* [{file_name}]({download_url})<br> *Page label:* {page_label}")
        except Exception as e:
            log.exception("Error formatting source %s", e)
            continue
    
    return delimitter.join(_sources)