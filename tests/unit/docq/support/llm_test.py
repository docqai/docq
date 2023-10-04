"""Tests for docq.support.llm."""
from unittest.mock import Mock, patch

from docq.model_selection.main import ModelUsageSettingsCollection
from docq.support.llm import run_chat
from llama_index import ServiceContext
from llama_index.chat_engine import SimpleChatEngine


def test_run_chat() -> None:
    """Test run chat."""
    with patch.object(SimpleChatEngine, "from_defaults") as mock_simple_chat_engine, patch(
        "docq.support.llm._get_service_context"
    ) as mock_get_service_context:
        mock_get_service_context.return_value = Mock(ServiceContext)
        mocked_engine = Mock(SimpleChatEngine)
        mock_simple_chat_engine.return_value = mocked_engine
        mocked_chat = Mock()
        mocked_engine.chat = mocked_chat
        mocked_chat.return_value = "LLM response"
        mocked_model_usage_settings_collection = Mock(ModelUsageSettingsCollection)

        response = run_chat("My ask", "My chat history", mocked_model_usage_settings_collection)
        mocked_chat.assert_called_once_with("My ask")
        assert response == "LLM response"
