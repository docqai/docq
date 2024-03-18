"""Integration tests for the Optimum embedding module."""

import logging
import unittest
from unittest.mock import MagicMock, Mock, patch

from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_spaces import _create_document_summary_index, _persist_index
from docq.model_selection.main import (
    LLM_SERVICE_INSTANCES,
    LlmUsageSettings,
    LlmUsageSettingsCollection,
    ModelCapability,
)
from docq.support import llm
from llama_index.core.schema import Document


class TestCreateDocumentSummaryIndex(unittest.TestCase):
    def setUp(self) -> None:
        logging.getLogger().setLevel(logging.ERROR)

        self.MODEL_SETTINGS_COLLECTION = LlmUsageSettingsCollection(
            name="Azure OpenAI wth Local Embedding",
            key="azure_openai_with_local_embedding",
            model_usage_settings={
                ModelCapability.CHAT: LlmUsageSettings(
                    model_capability=ModelCapability.CHAT,
                    temperature=0.7,
                    service_instance_config=LLM_SERVICE_INSTANCES["azure-openai-gpt35turbo"],
                ),
                ModelCapability.EMBEDDING: LlmUsageSettings(
                    model_capability=ModelCapability.EMBEDDING,
                    service_instance_config=LLM_SERVICE_INSTANCES["optimum-bge-small-en-v1.5"],
                ),
            },
        )

        llm._init_local_models()  # download local models. this is run on app setup.

    # @patch("docq.manage_spaces._get_default_storage_context")
    # @patch("docq.manage_spaces._get_service_context")
    # @patch("docq.manage_spaces.DocumentSummaryIndex.from_documents")
    # @patch("docq.support.llm._get_generation_model")
    # @patch("docq.support.llm._callback_manager", new_callable=MagicMock)

    # @patch("llama_index.core.callbacks.base.CallbackManager", new_callable=MagicMock)
    # @patch("logging.getLogger")
    def test_create_document_summary_index(
        self,
        # mock_get_generation_model,
        # mock_from_documents, mock_get_service_context, mock_get_default_storage_context
    ):
        # Arrange

        document1 = Document(doc_id="1", text="This is the first document.")
        document2 = Document(doc_id="2", text="This is the second document.")
        documents = [document1, document2]

        model_settings_collection = self.MODEL_SETTINGS_COLLECTION

        # Act
        result_index = _create_document_summary_index(documents, model_settings_collection)
        _persist_index(result_index, SpaceKey(type_=SpaceType.SHARED, id_=9, org_id=9999, summary="test space"))
        result_nodes = result_index.as_retriever().retrieve("This is the first document.")

        # Assert
        assert len(result_nodes) == 1
