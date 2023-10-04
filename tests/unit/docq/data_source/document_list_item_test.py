"""A module for testing the DocumentList data structure serialisation."""

import sys
import tempfile
import unittest
from datetime import datetime
from typing import Self

from docq.data_source.azure_blob import AzureBlob
from docq.domain import DocumentListItem


class TestDocumentListSerialisation(unittest.TestCase):
    """A unittest class for testing the DocumentList data structure."""

    def setUp(self: Self) -> None:
        """Set up the test fixture."""
        self.document_list = [
            DocumentListItem(link="document1.pdf", indexed_on=1691416038.209924, size=1024234),
            DocumentListItem(link="document2.pdf", indexed_on=1691416038.209924, size=2048234),
        ]
        self.persist_path = tempfile.mkdtemp()
        self.filename = "document_list.json"

    def test_save_load_document_list(self: Self) -> None:
        """Test that the serialisation format in _save_document_list can be de-serialised by _load_document_list."""
        with tempfile.TemporaryDirectory() as persist_path:
            AzureBlob()._save_document_list(
                document_list=self.document_list, persist_path=persist_path, filename=self.filename
            )
            loaded_document_list = AzureBlob()._load_document_list(persist_path=persist_path, filename=self.filename)
            assert loaded_document_list == self.document_list

    def test_create_instance_method(self: Self) -> None:
        """Test that the create_instance method works as expected."""
        document_link = "document1.pdf"
        document_text = "This is the text of the document."
        document_list_item = DocumentListItem.create_instance(document_link=document_link, document_text=document_text)
        assert document_list_item.link == document_link
        assert document_list_item.indexed_on is not None
        self.assertAlmostEqual(  # noqa: PT009
            document_list_item.indexed_on,
            datetime.timestamp(datetime.now().utcnow()),
            delta=5,
        )
        assert document_list_item.indexed_on
        assert document_list_item.size == sys.getsizeof(document_text)
