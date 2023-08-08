"""Functions to manage documents."""
import logging as log
import os
import shutil
import unicodedata
from datetime import datetime
from mimetypes import guess_type
from typing import DefaultDict

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

def _remove_ascii_control_characters(text: str) -> str:
    """Remove ascii control characters from the text."""
    return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")

def _parse_metadata(metadata: dict) -> tuple:
    """Parse the metadata."""
    s_type = metadata.get(str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower())
    uri = metadata.get(str(DocumentMetadata.SOURCE_URI.name).lower())
    if s_type == "SpaceDataSourceWebBased":
        website = _remove_ascii_control_characters(metadata.get("source_website"))
        page_title = _remove_ascii_control_characters(metadata.get("page_title"))
        return website, page_title, uri, s_type
    # File based data source
    file_name = metadata.get("file_name")
    page_label = metadata.get("page_label")
    return file_name, page_label, uri, s_type

def _group_file_sources(name: str, uri: str, page: str, sources: dict) -> str:
    """Group the sources."""
    if not name or not uri or not page:
        return # Skip if any of the required fields are missing
    if uri in sources:
        sources[uri].append(page)
    else:
        sources[uri] = [name, page]

def _group_web_sources(website: str, uri: str, page_title: str, sources: dict) -> str:
    """Group the sources."""
    if not website or not uri or not page_title:
        return # Skip if any of the required fields are missing
    if website in sources:
        sources[website].append((page_title, uri))
    else:
        sources[website] = [(page_title, uri)]

def _generate_file_markdown(file_sources: dict) -> str:
    """Template to generate markdown for listing file sources."""
    file_sources_markdown = ""
    for uri, sources in file_sources.items():
        name, pages = sources[0], list(set(sources[1:]))
        file_sources_markdown += f"> **File:** ({name})[{_get_download_link(name, uri)}]<br> **Pages:** {', '.join(pages)}\n\n"
    return file_sources_markdown

def _generate_web_markdown(web_sources: dict) -> str:
    """Template to generate markdown for listing web sources."""
    web_sources_markdown = ""
    site_delimiter = "\n>- "
    for website, page in web_sources.items():
        unique_pages = list(set(page))
        page_list_str = "\n>- ".join([f"[{page_title}]({uri})" for page_title, uri in unique_pages])
        web_sources_markdown += f"\n> ###### {website}{site_delimiter if page_list_str else ''}{page_list_str}{page_list_str}\n"
    return web_sources_markdown + "\n"

def format_document_sources(source_nodes: list[NodeWithScore]) -> str:
    """Format document sources."""
    file_sources = DefaultDict(list)
    web_sources = DefaultDict(list)

    try:
        for source_node in source_nodes:
            metadata = source_node.node.metadata
            if metadata:
                name, page, uri, s_type = _parse_metadata(metadata)
                if s_type == "SpaceDataSourceWebBased":
                    web_sources = _group_web_sources(name, uri, page, web_sources)
                else:
                    file_sources = _group_file_sources(name, uri, page, file_sources)

        total = len(file_sources) + len(web_sources)
        fmt_sources = f"\n##### Source{'s' if total > 1 else ''}:\n" + _generate_file_markdown(file_sources) + _generate_web_markdown(web_sources)
        return fmt_sources if total > 0 else ""

    except Exception as e:
        log.error("Error formatting document sources: %s", e)
