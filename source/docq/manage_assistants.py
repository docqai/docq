"""prompt templates that represent a persona."""
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Optional

from llama_index import ChatPromptTemplate
from llama_index.llms.base import ChatMessage, MessageRole

from .domain import Assistant, AssistantType
from .support.store import (
    get_sqlite_global_system_file,
    get_sqlite_org_system_file,
)

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
SQL_CREATE_ASSISTANTS_TABLE = """
CREATE TABLE IF NOT EXISTS assistants (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE, -- friendly display name
    type TEXT, -- persona_type enum
    archived BOOL DEFAULT 0,
    system_prompt_template TEXT, -- py format string template
    user_prompt_template TEXT, -- py format string template
    llm_settings_collection_key TEXT, -- key for a valid Docq llm settings collection
    space_group_id INTEGER, -- space_group_id for knowledge
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

ASSISTANT = tuple[int, str, str, bool, str, str, str, datetime, datetime]

def _init(org_id: Optional[int] = None) -> None:
    """Initialize the database.

    Needs to be called twice with the current context org_id and without org_id, to create the global scope table and the org scope table.

    Args:
        org_id (Optional[int]): The org id. If None then will initialise the global scope table.
    """
    with closing(
        sqlite3.connect(__get_assistants_sqlite_file(org_id=org_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_ASSISTANTS_TABLE)
        connection.commit()

def llama_index_chat_prompt_template_from_persona(persona: Assistant) -> ChatPromptTemplate:
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


def get_personas_fixed(persona_type: Optional[AssistantType] = None) -> dict[str, Assistant]:
    """Get the personas."""
    result = {}
    if persona_type == AssistantType.SIMPLE_CHAT:
        result = {key: Assistant(key=key, **persona) for key, persona in SIMPLE_CHAT_PERSONAS.items()}
    elif persona_type == AssistantType.AGENT:
        result = {key: Assistant(key=key, **persona) for key, persona in AGENT_PERSONAS.items()}
    elif persona_type == AssistantType.ASK:
        result = {key: Assistant(key=key, **persona) for key, persona in ASK_PERSONAS.items()}
    else:
        result = {
            **{key: Assistant(key=key, **persona) for key, persona in SIMPLE_CHAT_PERSONAS.items()},
            **{key: Assistant(key=key, **persona) for key, persona in AGENT_PERSONAS.items()},
            **{key: Assistant(key=key, **persona) for key, persona in ASK_PERSONAS.items()},
        }
    return result


def get_assistant_or_default(assistant_id: Optional[int] = None, org_id: Optional[int] = None) -> Assistant:
    """Get the persona."""
    if assistant_id:
        assistant_data = get_assistant(assistant_id=assistant_id, org_id=org_id)
        return Assistant(
            key=str(assistant_data[0]),
            name=assistant_data[1],
            system_prompt_content=assistant_data[4],
            user_prompt_template_content=assistant_data[5],
            llm_settings_collection_key=assistant_data[6],
        )
    else:
        key = "default"
        return Assistant(key=key, **SIMPLE_CHAT_PERSONAS[key])


def list_assistants(org_id: Optional[int] = None) -> list[ASSISTANT]:
    """List the assistants.

    Args:
        org_id (Optional[int]): The current org id. If None then will try to get from global scope table.
    """
    if org_id:
        _init(org_id)

    with closing(
        sqlite3.connect(__get_assistants_sqlite_file(org_id=org_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT id, name, type, archived, system_prompt_template, user_prompt_template, llm_settings_collection_key, created_at, updated_at FROM assistants")
        rows = cursor.fetchall()
        return [(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]) for row in rows]

def get_assistant(assistant_id: int, org_id: Optional[int]) -> ASSISTANT:
    """Get the assistant.

    If just assistant_id then will try to get from global scope table.
    """
    if org_id:
        _init(org_id)

    with closing(
        sqlite3.connect(__get_assistants_sqlite_file(org_id=org_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT id, name, type, archived, system_prompt_template, user_prompt_template, llm_settings_collection_key, created_at, updated_at FROM assistants WHERE id = ?", (assistant_id,))
        row = cursor.fetchone()
        if row is None:
            if org_id:
                raise ValueError(f"No Persona with: id = '{assistant_id}' that belongs to org org_id= '{org_id}'")
            else:
                raise ValueError(f"No Persona with: id = '{assistant_id}' in global scope.")
        return (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])

def create_or_update_assistant(
    name: str,
    assistant_type: AssistantType,
    archived: bool,
    system_prompt_template: str,
    user_prompt_template: str,
    llm_settings_collection_key: str,
    assistant_id: Optional[int] = None,
    org_id: Optional[int] = None,
) -> int | None:
    """Create or update a persona.

    If user_id and org_id are None then will try to create or update in global scope table.

    Args:
        name (str): The name.
        assistant_type (AssistantType): The type.
        archived (bool): The archived.
        system_prompt_template (str): The system prompt template.
        user_prompt_template (str): The user prompt template.
        llm_settings_collection_key (str): The LLM settings collection key.
        assistant_id (Optional[int]): The assistant id. If present then update else create.
        org_id (Optional[int]): The org id.

    Returns:
        int | None: The assistant ID if successful.
    """
    result_id = None
    if org_id:
        _init(org_id)

    print("assistant org_id: ", org_id)
    if assistant_id is None:
        sql = "INSERT INTO assistants (name, type, archived, system_prompt_template, user_prompt_template, llm_settings_collection_key) VALUES (?, ?, ?, ?, ?, ?)"
        params = (name, assistant_type.name, archived, system_prompt_template, user_prompt_template, llm_settings_collection_key)

    else:
        sql = "UPDATE assistants SET name = ?, type = ?, archived = ?, system_prompt_template = ?, user_prompt_template = ?, llm_settings_collection_key = ?, updated_at = ? WHERE id = ?"
        params = (name, assistant_type.name, archived, system_prompt_template, user_prompt_template, llm_settings_collection_key, datetime.utcnow(), assistant_id)
        result_id = assistant_id

    print("sql: ", sql)
    print("params: ", params)
    try:
        with closing(
            sqlite3.connect(__get_assistants_sqlite_file(org_id=org_id), detect_types=sqlite3.PARSE_DECLTYPES)
        ) as connection, closing(connection.cursor()) as cursor:
            cursor.execute(
                sql,
                params,
            )
            connection.commit()
            if assistant_id is None:
                result_id = cursor.lastrowid
    except Exception as e:
        raise e
    return result_id

def __get_assistants_sqlite_file(org_id: Optional[int]) -> str:
    """Get the SQLite file for a assistants based on scope.

    If org_id is None then will return the global scope file otherwise the org scope file.
    """
    path = ""
    # if user_id:
    #     path = get_sqlite_user_system_file(user_id)
    if org_id:  # noqa: SIM108
        path = get_sqlite_org_system_file(org_id)
    else:
        path = get_sqlite_global_system_file()
    return path
