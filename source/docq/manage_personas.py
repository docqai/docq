"""prompt templates that represent a persona."""
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Optional

from llama_index import ChatPromptTemplate
from llama_index.llms.base import ChatMessage, MessageRole

from .domain import Persona, PersonaType
from .support.store import (
    _DataScope,
    get_sqlite_global_system_file,
    get_sqlite_org_system_file,
    get_sqlite_user_system_file,
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
SQL_CREATE_PERSONAS_TABLE = """
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

PERSONA = tuple[int, str, str, bool, str, str, str, datetime, datetime]


# def _init() -> None:
#     """Initialize the database."""
#     _init_orgs_scope_table()
#     _init_user_scope_table()
#     # we'll leave global personas hard coded for now.

# def _init_orgs_scope_table() -> None:
#     """Initialize the database."""
#     with closing(
#         sqlite3.connect(get_sqlite_org_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
#     ) as connection, closing(connection.cursor()) as cursor:
#         cursor.execute(SQL_CREATE_PERSONAS_TABLE)
#         connection.commit()

# def _init_user_scope_table() -> None:
#     with closing(
#         sqlite3.connect(get_sqlite_user_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
#     ) as connection, closing(connection.cursor()) as cursor:
#         cursor.execute(SQL_CREATE_PERSONAS_TABLE)
#         connection.commit()


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


def get_personas_fixed(persona_type: Optional[PersonaType] = None) -> dict[str, Persona]:
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


def get_persona_fixed(key: str) -> Persona:
    """Get the persona."""
    if key not in SIMPLE_CHAT_PERSONAS:
        raise ValueError(f"No Persona with: {key}")
    return Persona(key=key, **SIMPLE_CHAT_PERSONAS[key])




def list_personas(persona_id: int, user_id: Optional[int], org_id: Optional[int]) -> list[PERSONA]:
    """List the personas."""
    with closing(
        sqlite3.connect(_get_persona_sqlite_file(user_id=user_id, org_id=org_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT id, name, type, archived, system_prompt_template, user_prompt_template, model_settings_collection_key, created_at, modified_at FROM personas")
        rows = cursor.fetchall()
        # return as list of tuple of PERSONA
        return [(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]) for row in rows]

def get_persona(persona_id: int, user_id: Optional[int], org_id: Optional[int]) -> PERSONA:
    """Get the persona.

    If just persona_id then will try to get from global scope table.
    """
    with closing(
        sqlite3.connect(_get_persona_sqlite_file(user_id=user_id, org_id=org_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT id, name, type, archived, system_prompt_template, user_prompt_template, model_settings_collection_key, created_at, modified_at FROM personas WHERE id = ?", (persona_id,))
        row = cursor.fetchone()
        if row is None:
            if user_id:
                raise ValueError(f"No Persona with: id = '{persona_id}' that belongs to user user_id= '{user_id}'")
            elif org_id:
                raise ValueError(f"No Persona with: id = '{persona_id}' that belongs to org org_id= '{org_id}'")
            else:
                raise ValueError(f"No Persona with: id = '{persona_id}' in global scope.")
        return (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])

def create_or_update_persona(
    name: str,
    persona_type: PersonaType,
    archived: bool,
    system_prompt_template: str,
    user_prompt_template: str,
    model_settings_collection_key: str,
    persona_id: Optional[int],
    user_id: Optional[int],
    org_id: Optional[int],
) -> None:
    """Create or update a persona.

    If user_id and org_id are None then will try to create or update in global scope table.

    Args:
        name (str): The name.
        persona_type (PersonaType): The type.
        archived (bool): The archived.
        system_prompt_template (str): The system prompt template.
        user_prompt_template (str): The user prompt template.
        model_settings_collection_key (str): The model settings collection key.
        persona_id (Optional[int]): The persona id. If present then update else create.
        user_id (Optional[int]): The user id.
        org_id (Optional[int]): The org id.
    """
    if persona_id is None:
        sql = "INSERT INTO personas (name, type, archived, system_prompt_template, user_prompt_template, model_settings_collection_key) VALUES (?, ?, ?, ?, ?, ?,  )"
        params = (name, persona_type.name, archived, system_prompt_template, user_prompt_template, model_settings_collection_key)

    else:
        sql = "UPDATE personas SET name = ?, type = ?, archived = ?, system_prompt_template = ?, user_prompt_template = ?, model_settings_collection_key = ? WHERE id = ?"
        params = (name, persona_type.name, archived, system_prompt_template, user_prompt_template, model_settings_collection_key, persona_id)

    with closing(
        sqlite3.connect(_get_persona_sqlite_file(user_id=user_id, org_id=org_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            sql,
            params,
        )
        connection.commit()

def _get_persona_sqlite_file(org_id: Optional[int], user_id: Optional[int]) -> str:
    """Get the SQLite file for a persona."""
    path = ""
    if user_id:
        path = get_sqlite_user_system_file(user_id)
    elif org_id:
        path = get_sqlite_org_system_file(org_id)
    else:
        path = get_sqlite_global_system_file()
    return path
