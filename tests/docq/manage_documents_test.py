#!/usr/bin/env python3
"""Test manage_documents.py."""


import os
from contextlib import suppress
from shutil import rmtree

import pytest
from docq.domain import SpaceKey
from docq.manage_documents import _get_download_link, format_document_sources
from llama_index.schema import NodeWithScore, TextNode

node_text = """
page_label: 0
file_name: test.txt
Mock text
"""
# mock_node = TextNode(text=node_text, "test", [1, 2, 3], "test")
mock_node = TextNode(text=node_text, hash="test", metadata_template="page_label: 2, file_name: test")
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


# TODO: Redefine test with to with the different data source types
# @pytest.mark.parametrize(
#     ("source_nodes", "space", "expected"),
#     [
#         ([], "personal_1234", ""),
#         ([mock_node_with_score], "personal_1234", "> *File:* [test.txt]()<br> *Pages:* 0"),
#         (["failing-node"], "personal_1234", ""),
#     ],
# )
# def test_format_document_sources(source_nodes: list[NodeWithScore], space: SpaceKey, expected: str) -> None:
#     """Test that the document sources are formatted correctly."""
#     assert format_document_sources(source_nodes, space) == expected
