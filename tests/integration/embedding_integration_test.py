"""Integration tests for the Optimum embedding module."""

import logging
import unittest

from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_spaces import _create_vector_index, _persist_index
from docq.model_selection.main import (
    LLM_SERVICE_INSTANCES,
    LlmUsageSettings,
    LlmUsageSettingsCollection,
    ModelCapability,
)
from docq.support import llm
from llama_index.core.schema import Document


class TestCreateIndex(unittest.TestCase):
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

    def test_create_vector_index(
        self,
    ):
        # Arrange

        document1 = Document(doc_id="1", text="This is the first document.")
        document2 = Document(doc_id="2", text="This is the second document.")
        documents = [document1, document2]

        model_settings_collection = self.MODEL_SETTINGS_COLLECTION

        # Act
        # result_index = _create_document_summary_index(documents, model_settings_collection)
        result_index = _create_vector_index(documents, model_settings_collection)
        _persist_index(result_index, SpaceKey(type_=SpaceType.SHARED, id_=9, org_id=9999, summary="test space"))
        result_nodes = result_index.as_retriever().retrieve("This is the first document.")

        # Assert
        assert len(result_nodes) == 2
        assert result_nodes[0].text == "This is the first document."
