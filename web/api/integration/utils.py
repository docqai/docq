"""Slack utility functions."""

import docq.integrations.slack.manage_slack as manage_slack
from docq.integrations.slack.manage_slack_messages import (
    get_slack_thread_messages_as_chat_messages,
)
from docq.manage_assistants import get_personas_fixed
from docq.model_selection.main import get_model_settings_collection, get_saved_model_settings_collection
from docq.support.llm import run_ask, run_chat


def chat_completion(text: str) -> str:
    """Middleware to handle chat completion."""
    input_ = text
    history = []
    model_settings_collection = get_model_settings_collection("azure_openai_latest")
    assistant = get_personas_fixed(model_settings_collection.key)["default"]
    response = run_chat(input_, history, model_settings_collection, assistant)
    return response.response


def rag_completion(text: str, channel_id: str, thread_ts: str) -> str:
    """RAG based on the space group configured for the channel + thread messages."""
    spaces = manage_slack.get_rag_spaces(channel_id)
    org_id = manage_slack.get_org_id_from_channel_id(channel_id)

    response = "I am sorry, something went wrong."
    if org_id:
        # thread_messages = list_slack_thread_messages(channel_id, org_id, thread_ts)

        if not spaces:
            response = "This channel is not configured in Docq. Please contact your administrator to setup the channel.\nhttps://docq.ai"

        history = get_slack_thread_messages_as_chat_messages(channel_id, org_id, thread_ts)
        model_collection_settings = get_saved_model_settings_collection(org_id)
        assistant = get_personas_fixed(model_collection_settings.key)[
            "default"
        ]  # TODO: switch to using an assistant that saved so we can adjust per org.
        response = run_ask(text, history, model_collection_settings, assistant, spaces)

    return str(response.response) if response else "I am sorry, I could not find any relevant information." # type: ignore
