"""A module for testing the DocumentList data structure serialisation."""

import tempfile
import unittest

from docq.data_source.azure_blob import AzureBlob
from docq.domain import DocumentListItem


class TestDocumentListSerialisation(unittest.TestCase):
    """A unittest class for testing the DocumentList data structure."""

    def setUp(self) -> None:
        self.document_list = [
            DocumentListItem(link="document1.pdf", indexed_on=1691416038.209924, size=1024234),
            DocumentListItem(link="document2.pdf", indexed_on=1691416038.209924, size=2048234),
        ]
        self.persist_path = tempfile.mkdtemp()
        self.filename = "document_list.json"

    def test_save_load_document_list(self):
        """Test that the serialisation format in _save_document_list can be de-serialised by _load_document_list."""
        with tempfile.TemporaryDirectory() as persist_path:
            AzureBlob()._save_document_list(
                document_list=self.document_list, persist_path=persist_path, filename=self.filename
            )
            loaded_document_list = AzureBlob()._load_document_list(persist_path=persist_path, filename=self.filename)
            assert loaded_document_list == self.document_list
