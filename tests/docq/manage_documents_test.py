"""Test manage_documents.py."""
import unittest
from typing import Self
from unittest.mock import MagicMock, Mock, patch

from docq.manage_documents import (
    _classify_file_sources,
    _classify_web_sources,
    _generate_file_markdown,
    _generate_web_markdown,
    _get_download_link,
    _parse_metadata,
    _remove_ascii_control_characters,
    format_document_sources,
)


class TestManageDocuments(unittest.TestCase):
    """Test manage_documents."""

    def setUp(self: Self) -> None:
        """Prepare test data."""
        self.web_metadata = {"source_website": "https://example.net", "page_title": "page_title", "data_source_type": "SpaceDataSourceWebBased", "source_uri": "source_uri"}
        self.file_metadata = {"file_name": "file_name", "page_label": "page_label", "data_source_type": "SpaceDataSourceFileBased", "source_uri": "source_uri"}
        self.web_source_node = []
        node = MagicMock()
        node.metadata = self.web_metadata
        self.web_source_node.append(Mock(node=node, score=1))

        # file_source_node
        file_node = MagicMock()
        self.file_source_node = []
        file_node.metadata = self.file_metadata
        self.file_source_node.append(Mock(node=file_node, score=1))
        self.source_template = "\n##### Source:\n{file_sources}"

    def test_remove_asccii_control_characters(self: Self) -> None:
        """Test _remove_ascii_control_characters."""
        assert _remove_ascii_control_characters("abc") == "abc"
        assert _remove_ascii_control_characters("abc\ndef ") == "abcdef"
        assert _remove_ascii_control_characters("abc\ndef\x00xyz") == "abcdefxyz"

    def test_parse_metadata(self: Self) -> None:
        """Test parse_metadata."""
        assert _parse_metadata(self.file_metadata) == ("file_name", "page_label", "source_uri", "SpaceDataSourceFileBased")
        assert _parse_metadata(self.web_metadata) == ("https://example.net", "page_title", "source_uri", "SpaceDataSourceWebBased")

    def test_classify_file_sources(self: Self) -> None:
        """Test _classify_file_sources."""
        sources = _classify_file_sources("name", "uri", "page")
        assert sources == {"uri": ["name", "page"]}
        sources = _classify_file_sources("name", "uri", "page1", sources)
        assert sources == {"uri": ["name", "page", "page1"]}

    def test_classify_web_sources(self: Self) -> None:
        """Test _classify_web_sources."""
        sources = _classify_web_sources("website", "uri", "page_title")
        assert sources == {"website": [("page_title", "uri")]}

    @patch("docq.manage_documents._get_download_link")
    def test_generate_file_markdown(self: Self, download_link: Mock) -> None:
        """Test _generate_file_markdown."""
        sources = {"uri": ["name", "page", "page"]}
        download_link.return_value = "https://some_link.host"

        assert _generate_file_markdown(sources) == "> *File:* [name](https://some_link.host)<br> *Pages:* page\n\n"

    def test_generate_web_markdown(self: Self) -> None:
        """Test _generate_web_markdown."""
        sources = {"website": [("page_title", "uri"), ("page_title", "uri")]}
        assert _generate_web_markdown(sources) == "\n> ###### website\n>- [page_title](uri)\n\n"

    def test_get_download_link(self: Self) -> None:
        """Test _get_download_link."""
        assert _get_download_link("name", "uri") == "#"

    @patch("docq.manage_documents._get_download_link")
    def test_format_document_sources(self: Self, file_link: Mock) -> None:
        """Test format_document_sources."""
        file_link.return_value = "https://some_link.host"
        file_template = "> *File:* [file_name](https://some_link.host)<br> *Pages:* page_label\n\n"
        web_template = "\n> ###### https://example.net\n>- [page_title](source_uri)\n\n"

        assert format_document_sources(self.file_source_node) == self.source_template.format(file_sources=file_template), "File source should return a matching file template"
        assert format_document_sources(self.web_source_node) == self.source_template.format(file_sources=web_template), "Web source should return a matching web template"
        assert format_document_sources({}) == "", "Empty source should return empty string"
