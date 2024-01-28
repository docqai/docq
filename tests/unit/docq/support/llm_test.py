"""Tests for docq.support.llm."""
from typing import Dict
from unittest.mock import Mock, patch

from docq.manage_personas import Persona
from docq.model_selection.main import LlmUsageSettings, LlmUsageSettingsCollection, ModelCapability
from llama_index import ServiceContext
from llama_index.chat_engine import SimpleChatEngine


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
        mocked_persona = Mock(Persona)
        mocked_persona.system_prompt_content= "Some system prompt"
        mocked_persona.user_prompt_template_content = "My user prompt template"

        response = run_chat("My ask", "My chat history", mocked_model_usage_settings_collection, mocked_persona)
        mocked_chat.assert_called_once_with("My ask")
        assert response == "LLM response"
