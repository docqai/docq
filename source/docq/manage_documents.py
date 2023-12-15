"""Functions to manage documents."""
import logging as log
import os
import shutil
import unicodedata
from datetime import datetime
from mimetypes import guess_type
from typing import Optional

from llama_index.schema import NodeWithScore
from streamlit import runtime

from .data_source.main import DocumentMetadata
from .domain import FeatureKey, SpaceKey
from .manage_spaces import reindex
from .support.store import get_chat_thread_upload_file, get_upload_dir, get_upload_file


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


def save_thread_upload(filename: str, content: bytes, feature: FeatureKey, thread_id: str) -> None:
    """Upload the file to the space."""
    with open(get_chat_thread_upload_file(feature, thread_id, filename), "wb") as f:
        f.write(content)


def delete_thread_uploads(feature: FeatureKey, thread_id: str) -> None:
    """Delete the file from the space."""
    shutil.rmtree(get_chat_thread_upload_file(feature, thread_id))


def _is_web_address(uri: str) -> bool:
    """Return true if the uri is a web address."""
    return uri.startswith("http://") or uri.startswith("https://")


def _get_download_link(filename: str, path: str) -> str:
    """Return the download link for the file if runtime exists, otherwise return an empty string."""
    if _is_web_address(path):
        return path

    elif runtime.exists() and os.path.isfile(path):
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
    return "".join(ch for ch in text if unicodedata.category(ch)[0] != "C").strip()


def _parse_metadata(metadata: dict) -> tuple:
    """Parse the metadata."""
    s_type = metadata.get(str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower())
    uri = metadata.get(str(DocumentMetadata.SOURCE_URI.name).lower())
    if s_type == "SpaceDataSourceWebBased":
        website = _remove_ascii_control_characters(metadata.get("source_website", ""))
        page_title = _remove_ascii_control_characters(metadata.get("page_title", ""))
        return website, page_title, uri, s_type
    else:
        file_name = metadata.get("file_name")
        page_label = metadata.get("page_label")
        return file_name, page_label, uri, s_type


def _classify_file_sources(name: str, uri: str, page: str, sources: Optional[dict] = None) -> dict:
    """Classify file sources for easy grouping."""
    if sources is None:
        sources = {}
    if uri in sources:
        sources[uri].append(page)
    else:
        sources[uri] = [name, page]
    return sources


def _classify_web_sources(website: str, uri: str, page_title: str, sources: Optional[dict] = None) -> dict:
    """Classify web sources for easy grouping."""
    if sources is None:
        sources = {}
    if website in sources:
        sources[website].append((page_title, uri))
    else:
        sources[website] = [(page_title, uri)]
    return sources


def _generate_file_markdown(file_sources: dict) -> str:
    """Generate markdown for listing file sources."""
    markdown_list = []
    for uri, sources in file_sources.items():
        name, pages = sources[0], list(set(sources[1:]))
        download_link = _get_download_link(name, uri)
        markdown_list.append(f"> *File:* [{name}]({download_link})<br> *Pages:* {', '.join(pages)}")
    return "\n\n".join(markdown_list) + "\n\n" if markdown_list else ""


def _generate_web_markdown(web_sources: dict) -> str:
    """Generate markdown for listing web sources."""
    markdown_list = []
    site_delimiter = "\n>- "
    for website, page in web_sources.items():
        unique_pages = list(set(page))  # Remove duplicate pages
        page_list_str = site_delimiter.join([f"[{page_title}]({uri})" for page_title, uri in unique_pages])
        markdown_list.append(f"\n> ###### {website}{site_delimiter if page_list_str else ''}{page_list_str}")
    return "\n\n".join(markdown_list) + "\n\n" if markdown_list else ""


def format_document_sources(source_nodes: list[NodeWithScore]) -> str:
    """Format document sources."""
    file_sources = {}
    web_sources = {}
    log.debug("format_document_sources() Source node count: %s", len(source_nodes))
    for source_node in source_nodes:
        metadata = source_node.node.metadata
        if metadata:
            name, page, uri, s_type = _parse_metadata(metadata)
            log.debug("Source: %s", s_type)
            if s_type == "SpaceDataSourceWebBased":
                web_sources = _classify_web_sources(name, uri, page, web_sources)
            elif s_type == "SpaceDataSourceFileBased":
                file_sources = _classify_file_sources(name, uri, page, file_sources)
            else:
                log.warning("Unknown source type: %s. uri: %s, Node ID: %s", s_type, uri, source_node.node.id_)
    total = len(file_sources) + len(web_sources)
    fmt_sources = (
        f"\n##### Source{'s' if total > 1 else ''}:\n"
        + _generate_file_markdown(file_sources)
        + _generate_web_markdown(web_sources)
    )
    return fmt_sources if total else ""
