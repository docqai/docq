"""Slack utility functions."""

from docq.manage_assistants import get_personas_fixed
from docq.model_selection.main import get_model_settings_collection
from docq.support.llm import run_chat


def chat_completion(text: str) -> str:
    """Middleware to handle chat completion."""
    input_ = text
    history = ""
    model_settings_collection = get_model_settings_collection("azure_openai_latest")
    assistant = get_personas_fixed(model_settings_collection.key)["default"]
    response = run_chat(input_, history, model_settings_collection, assistant)
    return response.response
