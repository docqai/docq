"""Test manage_documents.py."""
import os
import tempfile
import unittest
from typing import Self
from unittest.mock import MagicMock, Mock, patch


class TestManageDocuments(unittest.TestCase):
    """Test manage_documents."""

    def setUp(self: Self) -> None:
        """Prepare test data."""
        self.web_metadata = {
            "source_website": "https://example.net",
            "page_title": "page_title",
            "data_source_type": "SpaceDataSourceWebBased",
            "source_uri": "source_uri",
        }
        self.file_metadata = {
            "file_name": "file_name",
            "page_label": "page_label",
            "data_source_type": "SpaceDataSourceFileBased",
            "source_uri": "source_uri",
        }
        self.web_source_node = []
        web_node = MagicMock()
        web_node.metadata = self.web_metadata
        self.web_source_node.append(Mock(node=web_node, score=1))

        # file_source_node
        file_node = MagicMock()
        self.file_source_node = []
        file_node.metadata = self.file_metadata
        self.file_source_node.append(Mock(node=file_node, score=1))
        self.source_template = "\n##### Source:\n{file_sources}"

    @patch("docq.manage_documents.reindex")
    @patch("docq.manage_documents.get_upload_file")
    def test_upload(self: Self, get_upload_file: Mock, reindex: Mock) -> None:
        """Test upload."""
        with tempfile.NamedTemporaryFile() as temp_file:
            from docq.manage_documents import upload

            get_upload_file.return_value = temp_file.name
            space = Mock()
            file_content = bytes("test", "utf-8")
            upload(temp_file.name, file_content, space)

            reindex.assert_called_once_with(space)
            get_upload_file.assert_called_once_with(space, temp_file.name)
            assert os.path.exists(temp_file.name), f"Path {temp_file.name} should exist"
            assert os.path.isfile(temp_file.name), f"File {temp_file.name} should be a file"
            assert os.path.getsize(temp_file.name) == len(file_content), f"File {temp_file.name} should have content"

    @patch("docq.manage_documents.get_upload_file")
    def test_get_file(self: Self, get_upload_file: Mock) -> None:
        """Test get_file."""
        from docq.manage_documents import get_file

        space = Mock()
        file_name = "file_name"
        get_upload_file.return_value = file_name
        assert get_file(file_name, space) == file_name, "File name should match"
        get_upload_file.assert_called_once_with(space, file_name)

    @patch("docq.manage_documents.get_upload_file")
    def test_delete(self: Self, get_upload_file: Mock) -> None:
        """Test delete."""
        from docq.manage_documents import delete

        space = Mock()
        with tempfile.TemporaryDirectory() as temp_dir:
            file_name = os.path.join(temp_dir, "file_name")
            ctrl_file_name = os.path.join(temp_dir, ".file_name")
            open(file_name, "w").close()
            open(ctrl_file_name, "w").close()

            assert os.path.exists(file_name), f"File {file_name} should exist"
            get_upload_file.return_value = file_name
            delete(file_name, space)

            assert not os.path.exists(file_name), f"File {file_name} should not exist"
            assert os.path.exists(ctrl_file_name), f"Control file {ctrl_file_name} should exist"
            get_upload_file.assert_called_once_with(space, file_name)

    @patch("docq.manage_documents.reindex")
    @patch("docq.manage_documents.get_upload_dir")
    def test_delete_all(self: Self, get_upload_dir: Mock, reindex: Mock) -> None:
        """Test delete_all."""
        from docq.manage_documents import delete_all

        space = Mock()
        with tempfile.TemporaryDirectory() as temp_dir:
            upload_dir = os.path.join(temp_dir, "upload")
            os.mkdir(upload_dir)

            assert os.path.exists(upload_dir), f"Directory path {upload_dir} should exist"
            assert os.path.isdir(upload_dir), f"Directory {upload_dir} should be a directory"
            get_upload_dir.return_value = temp_dir
            delete_all(space)

            assert not os.path.exists(upload_dir), f"Directory {temp_dir} should not exist"
            get_upload_dir.assert_called_once_with(space)
            reindex.assert_called_once_with(space)

    def test_is_web_address(self: Self) -> None:
        """Test _is_web_address."""
        from docq.manage_documents import _is_web_address

        assert _is_web_address("http://example.net"), "http://example.net should pass as web address"
        assert _is_web_address("https://example.net"), "https://example.net should pass as web address"
        assert not _is_web_address("example.net"), "example.net should not pass as web address"

    def test_remove_ascii_control_characters(self: Self) -> None:
        """Test _remove_ascii_control_characters."""
        from docq.manage_documents import _remove_ascii_control_characters

        assert _remove_ascii_control_characters("abc") == "abc"
        assert _remove_ascii_control_characters("abc\ndef ") == "abcdef"
        assert _remove_ascii_control_characters("abc\ndef\x00xyz") == "abcdefxyz"

    def test_parse_metadata(self: Self) -> None:
        """Test parse_metadata."""
        from docq.manage_documents import _parse_metadata

        assert _parse_metadata(self.file_metadata) == (
            "file_name",
            "page_label",
            "source_uri",
            "SpaceDataSourceFileBased",
        )
        assert _parse_metadata(self.web_metadata) == (
            "https://example.net",
            "page_title",
            "source_uri",
            "SpaceDataSourceWebBased",
        )

    def test_classify_file_sources(self: Self) -> None:
        """Test _classify_file_sources."""
        from docq.manage_documents import _classify_file_sources

        sources = _classify_file_sources("name", "uri", "page")
        assert sources == {"uri": ["name", "page"]}
        sources = _classify_file_sources("name", "uri", "page1", sources)
        assert sources == {"uri": ["name", "page", "page1"]}

    def test_classify_web_sources(self: Self) -> None:
        """Test _classify_web_sources."""
        from docq.manage_documents import _classify_web_sources

        sources = _classify_web_sources("website", "uri", "page_title")
        assert sources == {"website": [("page_title", "uri")]}
        sources = _classify_web_sources("website", "uri", "page_title", sources)
        assert sources == {"website": [("page_title", "uri"), ("page_title", "uri")]}

    @patch("docq.manage_documents._get_download_link")
    def test_generate_file_markdown(self: Self, download_link: Mock) -> None:
        """Test _generate_file_markdown."""
        from docq.manage_documents import _generate_file_markdown

        sources = {"uri": ["name", "page", "page"]}
        download_link.return_value = "https://some_link.host"

        assert _generate_file_markdown(sources) == "> *File:* [name](https://some_link.host)<br> *Pages:* page\n\n"

    def test_generate_web_markdown(self: Self) -> None:
        """Test _generate_web_markdown."""
        from docq.manage_documents import _generate_web_markdown

        sources = {"website": [("page_title", "uri"), ("page_title", "uri")]}
        assert _generate_web_markdown(sources) == "\n> ###### website\n>- [page_title](uri)\n\n"

    @patch("docq.manage_documents.runtime")
    def test_get_download_link(self: Self, runtime: Mock) -> None:
        """Test _get_download_link."""
        from docq.manage_documents import _get_download_link

        web_address = "https://example.net"

        assert _get_download_link("name", web_address) == web_address, "Web address should return the same address"

        runtime.exists = MagicMock(return_value=False)
        assert _get_download_link("name", "uri") == "#", "Download link should return '#' if runtime does not exist"

        add = MagicMock(return_value="https://some_link.host")
        get_instance = MagicMock(
            return_value=Mock(media_file_mgr=Mock(add=add))
        )

        runtime.exists = MagicMock(return_value=True)
        runtime.get_instance = get_instance
        with tempfile.NamedTemporaryFile() as temp_file:
            assert _get_download_link("name", temp_file.name) == "https://some_link.host", "Download link should be returned if runtime exists."

    @patch("docq.manage_documents._get_download_link")
    def test_format_document_sources(self: Self, file_link: Mock) -> None:
        """Test format_document_sources."""
        file_link.return_value = "https://some_link.host"
        file_template = "> *File:* [file_name](https://some_link.host)<br> *Pages:* page_label\n\n"
        web_template = "\n> ###### https://example.net\n>- [page_title](source_uri)\n\n"
        from docq.manage_documents import format_document_sources

        assert format_document_sources(self.file_source_node) == self.source_template.format(
            file_sources=file_template
        ), "File source should return a matching file template"
        assert format_document_sources(self.web_source_node) == self.source_template.format(
            file_sources=web_template
        ), "Web source should return a matching web template"
        assert format_document_sources([]) == "", "Empty source should return empty string"

        with patch("docq.manage_documents._parse_metadata", MagicMock(return_value=("name", "page", "uri", "UNKNOWN_DS"))):
            assert format_document_sources(self.file_source_node) == "", "Unknown data source should return empty string"
