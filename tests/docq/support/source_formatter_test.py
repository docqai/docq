"""Tests for docq.support.source_formatter."""
import unittest
from typing import Self
from unittest.mock import Mock

from docq.support.source_formatter import DocumentMetadata, format_document_sources


class TestDocumentSourceFormatter(unittest.TestCase):
    """Test the document source formatter."""
    def setUp(self: Self) -> None:
        """Set up the test."""
        self.node_with_score = Mock()
        self.node_with_score.node.metadata = {
            str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower(): 'SpaceDataSourceWebBased',
            'source_website': 'test_website',
            str(DocumentMetadata.SOURCE_URI.name).lower(): 'test_uri',
            'page_title': 'test_title',
        }

    def test_format_document_sources_with_valid_web_source(self: Self) -> None:
        """Test format document sources with valid web source."""
        result = format_document_sources([self.node_with_score])
        expected = '\n##### Source:\n \n> ###### test_website\n>- [test_title](test_uri)'
        assert result == expected

    def test_format_document_sources_with_invalid_web_source(self: Self) -> None:
        """Test format document sources with invalid web source."""
        self.node_with_score.node.metadata['source_website'] = None
        result = format_document_sources([self.node_with_score])
        assert result == "Unable to list sources."
