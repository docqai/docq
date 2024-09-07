"""Integration tests for the Optimum embedding module."""

import logging
import unittest
from typing import Self

from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_spaces import _create_vector_index, _persist_index
from docq.model_selection.main import (
    get_model_settings_collection,
)
from docq.support import llm
from llama_index.core.schema import Document


class TestCreateIndex(unittest.TestCase):
    """Integration tests for indexing related functionality."""

    def setUp(self: Self) -> None:
        logging.getLogger().setLevel(logging.ERROR)

        llm._init_local_models()  # download local models. this is run on app setup.

    def test_create_vector_index(
        self: Self,
    ) -> None:
        """Test creating a vector index. Indexes docs using local model. then checks retrieval."""
        # Arrange

        document1 = Document(doc_id="1", text="This is the first document.")
        document2 = Document(doc_id="2", text="This is the second document.")
        documents = [document1, document2]

        model_settings_collection = get_model_settings_collection("azure_openai_with_local_embedding")

        # Act
        # result_index = _create_document_summary_index(documents, model_settings_collection)
        result_index = _create_vector_index(documents, model_settings_collection)
        _persist_index(result_index, SpaceKey(type_=SpaceType.SHARED, id_=9, org_id=9999, summary="test space"))
        result_nodes = result_index.as_retriever().retrieve("This is the first document.")

        # Assert
        assert len(result_nodes) == 2
        assert result_nodes[0].text == "This is the first document."

    # def test_reindex_vector_index() -> None:
    #     """Test reindex. Check's that _persist_index() is called."""
    #     from docq.manage_spaces import reindex

    #     with patch("docq.manage_indices._persist_index") as mock_persist_index, patch(
    #         "docq.manage_indices._create_vector_index"
    #     ) as mock_create_vector_index, patch(
    #         "docq.manage_spaces.get_space_data_source"
    #     ) as mock_get_space_data_source, patch(
    #         "docq.data_source.manual_upload.ManualUpload.load"
    #     ) as mock_ManualUpload_load, patch(  # noqa: N806
    #         "docq.manage_spaces.get_saved_model_settings_collection"  # note the reference to the file where the function is called, not defined.
    #     ) as mock_get_saved_model_settings_collection, patch(
    #         "docq.manage_spaces.SpaceDataSources", new_callable=MagicMock
    #     ) as mock_SpaceDataSources:
    #         # ...

    #         mock_vector_index = Mock(VectorStoreIndex)
    #         mock_create_vector_index.return_value = mock_vector_index

    #         mock_get_space_data_source.return_value = ("MANUAL_UPLOAD", {})

    #         # mock_ManualUpload_load.return_value = [

    #         # ]

    #         mock_SpaceDataSources.__getitem__.return_value.value.load.return_value = [
    #             Document(doc_id="testid", text="test", extra_info={"source_uri": "https://example.com}"})
    #         ]

    #         arg_space_key = SpaceKey(SpaceType.SHARED, 1234, 4567, "this is a test space with mocked data")

    #         mock_get_saved_model_settings_collection.return_value = get_model_settings_collection(
    #             "azure_openai_with_local_embedding"
    #         )
    #         # print({mock_get_saved_model_settings_collection.return_value.__str__()})
    #         reindex(arg_space_key)

    #         mock_persist_index.assert_called_once_with(mock_vector_index, arg_space_key)
