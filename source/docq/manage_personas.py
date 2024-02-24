"""prompt templates that represent a persona."""
import sqlite3
from contextlib import closing
from os import system
from typing import Optional, Self

from llama_index import ChatPromptTemplate
from llama_index.llms.base import ChatMessage, MessageRole
from regex import P

from .domain import Persona, PersonaType
from .support.store import get_sqlite_system_file

DEFAULT_QA_SYSTEM_PROMPT = """You are an expert Q&A system that is trusted around the world. Always answer the query using the provided context information and chat message history, and not prior knowledge. Some rules to follow: 1. Never directly reference the given context in your answer. 2. Avoid statements like 'Based on the context, ...' or 'The context information ...' or '... given context information.' or anything along those lines."""

DEFAULT_QA_SYSTEM_PROMPT = """You are a friendly and helpful assistant."""


DEFAULT_QA_USER_PROMPT_TEMPLATE = """Chat message history is below:
            ---------------------
            {history_str}
            ---------------------
            Context information is below:
            ---------------------
            {context_str}
            ---------------------
            Given the context information and chat message history but not prior knowledge from your training,
            answer the query below in British English.
            Query: {query_str}
            Answer: """


SIMPLE_CHAT_PERSONAS = {
    "default": {
        "name": "General Q&A Assistant",
        "system_prompt_content": DEFAULT_QA_SYSTEM_PROMPT,
        "user_prompt_template_content": DEFAULT_QA_USER_PROMPT_TEMPLATE,
    },
    "elon-musk": {
        "name": "Elon Musk",
        "system_prompt_content": """You are Elon Musk, the CEO of Tesla and SpaceX.\n
            You are a billionaire entrepreneur and engineer.\n
            You are a meme lord and have a cult following on Twitter.\n
            You are also a bit of a troll.\n
            You are a bit of a meme lord and have a cult following on Twitter.\n
            """,
        "user_prompt_template_content": """Chat message history is below:\n
            ---------------------\n
            {history_str}\n
            ---------------------\n\n
            Context information is below:\n
            ---------------------\n
            {context_str}\n
            ---------------------\n
            Given the context information and chat message history and your knowledge as Elon Musk from your training, 
            answer the query below.\n
            Query: {query_str}\n
            Answer: """,
    },
}


AGENT_PERSONAS = {}

ASK_PERSONAS = {
    "default": {
        "name": "General Q&A Assistant",
        "system_prompt_content": DEFAULT_QA_SYSTEM_PROMPT,
        "user_prompt_template_content": DEFAULT_QA_USER_PROMPT_TEMPLATE,
    },
    "meeting-assistant": {
        "name": "Meeting Assistant",
        "system_prompt_content": """You are a extremely helpful meeting assistant.
            You pay attention to all the details in a meeting.
            You are able summarise a meeting.
            You are able to answer questions about a meeting with context.
            Only answer questions using the meeting notes that are provided. Do NOT use prior knowledge.
            """,
        "user_prompt_template_content": """Chat message history is below:\n
            ---------------------\n
            {history_str}\n
            ---------------------\n\n
            Context information is below:\n
            ---------------------\n
            {context_str}\n
            ---------------------\n
            Given the meeting notes in the context information and chat message history, 
            answer the query below.\n
            Query: {query_str}\n
            Answer: """,
    },
}

# Keep DB schema simple an applicable to types of Gen models.
# The data model will provide further abstractions over this especially for things that map back to a system prompt or user prompt.
SQL_CREATE_ORGS_TABLE = """
CREATE TABLE IF NOT EXISTS personas (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE, -- friendly display name
    type TEXT, -- persona_type enum
    archived BOOL DEFAULT 0,
    system_prompt_template TEXT, -- py format string template
    user_prompt_template TEXT, -- py format string template
    model_settings_collection_key TEXT, -- key for a valid Docq model settings collection
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_ORGS_TABLE)
        connection.commit()





def llama_index_chat_prompt_template_from_persona(persona: Persona) -> ChatPromptTemplate:
    """Get the prompt template for the llama index."""
    _system_prompt_message = ChatMessage(
        content=persona.system_prompt_content,
        role=MessageRole.SYSTEM,
    )

    _user_prompt_message = ChatMessage(
        content=persona.user_prompt_template_content,
        role=MessageRole.USER,
    )

    return ChatPromptTemplate(message_templates=[_system_prompt_message, _user_prompt_message])


def get_personas(persona_type: Optional[PersonaType] = None) -> dict[str, Persona]:
    """Get the personas."""
    result = {}
    if persona_type == PersonaType.SIMPLE_CHAT:
        result = {key: Persona(key=key, **persona) for key, persona in SIMPLE_CHAT_PERSONAS.items()}
    elif persona_type == PersonaType.AGENT:
        result = {key: Persona(key=key, **persona) for key, persona in AGENT_PERSONAS.items()}
    elif persona_type == PersonaType.ASK:
        result = {key: Persona(key=key, **persona) for key, persona in ASK_PERSONAS.items()}
    else:
        result = {
            **{key: Persona(key=key, **persona) for key, persona in SIMPLE_CHAT_PERSONAS.items()},
            **{key: Persona(key=key, **persona) for key, persona in AGENT_PERSONAS.items()},
            **{key: Persona(key=key, **persona) for key, persona in ASK_PERSONAS.items()},
        }
    return result


def get_persona(key: str) -> Persona:
    """Get the persona."""
    if key not in SIMPLE_CHAT_PERSONAS:
        raise ValueError(f"No Persona with: {key}")
    return Persona(key=key, **SIMPLE_CHAT_PERSONAS[key])
