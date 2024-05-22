"""Tests for docq.support.llm."""
from unittest.mock import Mock, patch

from docq.domain import Assistant
from docq.model_selection.main import LlmUsageSettings, LlmUsageSettingsCollection, ModelCapability
from llama_index.core import ServiceContext
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.llms import ChatMessage, MessageRole


#@patch("docq.support.metadata_extractors.DEFAULT_MODEL_PATH")
def test_run_chat() -> None:
    """Test run chat."""
    from docq.support.llm import run_chat

    with patch.object(SimpleChatEngine, "from_defaults") as mock_simple_chat_engine, patch(
        "docq.support.llm._get_service_context"
    ) as mock_get_service_context:
        #mock_DEFAULT_MODEL_PATH.return_value = "./sfsdf"
        mock_get_service_context.return_value = Mock(ServiceContext)
        mocked_engine = Mock(SimpleChatEngine)
        mock_simple_chat_engine.return_value = mocked_engine
        mocked_chat = Mock()
        mocked_engine.chat = mocked_chat
        mocked_chat.return_value = "LLM response"
        mocked_model_usage_settings_collection = Mock(LlmUsageSettingsCollection)
        mocked_model_usage_settings = Mock(LlmUsageSettings)
        mocked_model_usage_settings.additional_args = {"arg1": "value1", "arg2": "value2"}
        mocked_model_usage_settings_collection.model_usage_settings = {ModelCapability.CHAT: mocked_model_usage_settings}
        mocked_assistant = Mock(Assistant)
        mocked_assistant.system_message_content = "Some system prompt"
        mocked_assistant.user_prompt_template_content = "My user prompt template"

        response = run_chat(
            "My ask",
            [ChatMessage(role=MessageRole.USER, content="My chat history")],
            mocked_model_usage_settings_collection,
            mocked_assistant,
        )
        mocked_chat.assert_called_once_with("My ask")
        assert response == "LLM response"
