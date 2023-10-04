"""Tests for the ManualUpload class."""

import unittest
from datetime import datetime
from typing import Self
from unittest.mock import MagicMock, patch

from docq.config import SpaceType
from docq.data_source.main import DocumentMetadata
from docq.data_source.manual_upload import ManualUpload
from docq.domain import DocumentListItem, SpaceKey


class TestManualUpload(unittest.TestCase):  # noqa: D101
    def setUp(self: Self) -> None:
        """Set up the test."""
        self.manual_upload = ManualUpload()

    def test_get_document_list(self: Self) -> None:
        """Test the get_document_list method."""
        space = SpaceKey(SpaceType.PERSONAL, 123, 345)
        configs = {}

        with patch("os.scandir") as mock_scandir, patch("docq.data_source.manual_upload.get_upload_dir"), patch(
            "os.DirEntry"
        ) as mock_os_dir_entry:
            file1 = mock_os_dir_entry()
            # use configure_mock because `dir_entry` has a property `name`
            file1.configure_mock(
                name="misc/test_files/Research-Revealing-the-True-GenAI-Data-Exposure-Risk.pdf",
                is_file=True,
            )
            file1.stat.return_value = MagicMock(st_ctime=1234567890, st_size=1024)

            mock_scandir.return_value = [file1]

            # Call the get_document_list method and test the result
            document_list = self.manual_upload.get_document_list(space, configs)

            assert document_list == [
                DocumentListItem(
                    "misc/test_files/Research-Revealing-the-True-GenAI-Data-Exposure-Risk.pdf",
                    1234567890,
                    1024,
                )
            ]

    def test_load(self: Self) -> None:
        """Test the load method including the metadata fields."""
        space = SpaceKey(SpaceType.PERSONAL, 123, 345)
        configs = {}

        with patch("docq.data_source.manual_upload.get_upload_dir") as mock_get_upload_dir:
            mock_get_upload_dir.return_value = "misc/test_files"

            documents = self.manual_upload.load(space, configs)

            assert len(documents) == 10
            assert documents[0].metadata[str(DocumentMetadata.SPACE_ID.name).lower()] == 123
            assert documents[0].metadata[str(DocumentMetadata.SPACE_TYPE.name).lower()] == "PERSONAL"
            assert documents[0].metadata[str(DocumentMetadata.DATA_SOURCE_NAME.name).lower()] == "Manual Upload"
            assert (
                documents[0].metadata[str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower()] == "SpaceDataSourceFileBased"
            )
            assert (
                documents[0].metadata[str(DocumentMetadata.SOURCE_URI.name).lower()]
                == "misc/test_files/Research-Revealing-the-True-GenAI-Data-Exposure-Risk.pdf"
            )
            assert (
                documents[0].metadata[str(DocumentMetadata.FILE_PATH.name).lower()]
                == "misc/test_files/Research-Revealing-the-True-GenAI-Data-Exposure-Risk.pdf"
            )
            self.assertAlmostEqual(  # noqa: PT009
                documents[0].metadata[str(DocumentMetadata.INDEXED_ON.name).lower()],
                datetime.timestamp(datetime.now().utcnow()),
                delta=5,
            )

            # SimpleDirectoryReader generated meta data fields that we depend on.
            assert documents[0].metadata["file_name"] == "Research-Revealing-the-True-GenAI-Data-Exposure-Risk.pdf"
            assert documents[0].metadata["page_label"] is not None
