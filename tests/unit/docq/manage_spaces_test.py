"""Tests for docq.manage_spaces module."""
import unittest
from unittest.mock import Mock, patch

from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_spaces import reindex
from docq.model_selection.main import get_model_settings_collection
from llama_index import Document, DocumentSummaryIndex


# def test_reindex() -> None:
#     """Test reindex."""
#     with patch("docq.manage_spaces._persist_index") as mock_persist_index, patch(
#         "docq.manage_spaces._create_index"
#     ) as mock_create_index, patch("docq.manage_spaces.get_space_data_source") as mock_get_space_data_source, patch(
#         "docq.data_source.manual_upload.ManualUpload.load"
#     ) as mock_ManualUpload_load, patch(  # noqa: N806
#         "docq.manage_spaces.get_saved_model_settings_collection"  # note the reference to the file where the function is called, not defined.
#     ) as mock_get_saved_model_settings_collection:  # noqa: N806
#         mock_index = Mock(GPTVectorStoreIndex)
#         mock_create_index.return_value = mock_index

#         mock_get_space_data_source.return_value = ("MANUAL_UPLOAD", {})
#         mock_ManualUpload_load.return_value = [
#             Document(doc_id="testid", text="test", metadata={"source_uri": "https://example.com}"})
#         ]
#         print("hello bla test running")

#         arg_space_key = SpaceKey(SpaceType.PERSONAL, 1234, 4567)

#         mock_get_saved_model_settings_collection.return_value = get_model_settings_collection("openai_latest")
#         print({mock_get_saved_model_settings_collection.return_value.__str__()})
#         reindex(arg_space_key)

#         mock_persist_index.assert_called_once_with(mock_index, arg_space_key)


def test_reindex_doc_summary_index() -> None:
    """Test reindex."""
    with patch("docq.manage_spaces._persist_index") as mock_persist_index, patch(
        "docq.manage_spaces._create_document_summary_index"
    ) as mock_create_document_summary_index, patch(
        "docq.manage_spaces.get_space_data_source"
    ) as mock_get_space_data_source, patch(
        "docq.data_source.manual_upload.ManualUpload.load"
    ) as mock_ManualUpload_load, patch(  # noqa: N806
        "docq.manage_spaces.get_saved_model_settings_collection"  # note the reference to the file where the function is called, not defined.
    ) as mock_get_saved_model_settings_collection:  # noqa: N806
        mock_index = Mock(DocumentSummaryIndex)
        mock_create_document_summary_index.return_value = mock_index

        mock_get_space_data_source.return_value = ("MANUAL_UPLOAD", {})

        mock_ManualUpload_load.return_value = [
            Document(doc_id="testid", text="test", metadata={"source_uri": "https://example.com}"})
        ]
        print("hello bla test running")

        arg_space_key = SpaceKey(SpaceType.PERSONAL, 1234, 4567, "this is a test space with mocked data")

        mock_get_saved_model_settings_collection.return_value = get_model_settings_collection("openai_latest")
        print({mock_get_saved_model_settings_collection.return_value.__str__()})
        reindex(arg_space_key)

        mock_persist_index.assert_called_once_with(mock_index, arg_space_key)
