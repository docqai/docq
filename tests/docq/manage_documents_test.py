#!/usr/bin/env python3
"""Test manage_documents.py."""


import os
from contextlib import suppress
from shutil import rmtree

import pytest
from docq.manage_documents import DocumentMetadata, _get_download_link, format_document_sources
from llama_index.schema import NodeWithScore, TextNode

metadata = {
    DocumentMetadata.SOURCE_URI.value: "https://example.com",
    DocumentMetadata.DATA_SOURCE_TYPE.value: "Manual Upload",
    DocumentMetadata.SPACE_TYPE.value: "PERSONAL",
    "file_name": "test.txt",
    "page_label": "0",
}
mock_node = TextNode(text="node_text", extra_info=metadata)
mock_node_with_score = NodeWithScore(node=mock_node, score=0.5)


@pytest.fixture(scope="module", autouse=True)
def setup() -> None:
    """Create a mock test directory and file and yield to the test function, then remove the mock test directory."""
    print("\x1b[1;34mSetting up manage_documents_test.py\x1b[0m")
    # create a mock test directory
    with suppress(FileExistsError):
        os.mkdir("test_dir")
    # Add a mock file to the test directory
    with open("test_dir/mock.txt", "w", encoding="utf-8") as f:
        f.write("test")
    yield  # type: ignore
    print("\x1b[1;34mTearing down manage_documents_test.py\x1b[0m")
    # remove the mock test directory
    rmtree("test_dir")
    return None


@pytest.mark.parametrize(
    ("filename", "path", "expected"),
    [
        ("test.txt", "test_dir/test.txt", ""),
        ("mock.txt", "test_dir/mock.txt", ""),
    ],
)
def test_get_download_link(filename: str, path: str, expected: str) -> None:
    """Test that the download link is returned correctly."""
    assert _get_download_link(filename, path) == expected


@pytest.mark.parametrize(
    ("source_nodes", "expected"),
    [
        ([mock_node_with_score], "> *File:* [test.txt]()<br> *Pages:* 0"),
    ],
)
def test_format_document_sources(source_nodes: list[NodeWithScore], expected: str) -> None:
    """Test that the document sources are formatted correctly."""
    assert format_document_sources(source_nodes) == expected
