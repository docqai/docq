"""Functions to run queries."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Literal, Optional

from llama_index.core.llms import ChatMessage, MessageRole

from docq.config import OrganisationFeatureType
from docq.domain import FeatureKey, SpaceKey
from docq.manage_assistants import Assistant
from docq.manage_documents import format_document_sources
from docq.model_selection.main import LlmUsageSettingsCollection
from docq.support.llm import query_error, run_ask, run_chat
from docq.support.store import (
    get_history_table_name,
    get_history_thread_table_name,
    get_public_sqlite_usage_file,
    get_sqlite_usage_file,
)

# TODO: add thread_space_id to hold the space that's hard attached to a thread for adhoc uploads
# add space_ids dict / array to loosely persist space ids that are selected by a user.
# add assistant_scoped_id to hold the assistant that's attached to the thread.
SQL_CREATE_THREAD_TABLE = """
CREATE TABLE IF NOT EXISTS {table} (
    id INTEGER PRIMARY KEY,
    topic TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


SQL_CREATE_MESSAGE_TABLE = """
CREATE TABLE IF NOT EXISTS {table} (
    id INTEGER PRIMARY KEY,
    message TEXT,
    human BOOL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thread_id INTEGER NOT NULL,
    FOREIGN KEY (thread_id) REFERENCES {thread_table} (id)
)
"""


MESSAGE_TEMPLATE = "{message}"

MESSAGE_WITH_SOURCES_TEMPLATE = "{message}\n{source}"

NUMBER_OF_MESSAGES_IN_HISTORY = 10


def _save_messages(data: list[tuple[str, bool, datetime, int]], feature: FeatureKey) -> list:
    """feature.id_ needs to be the user_id."""
    rows = []
    tablename = get_history_table_name(feature.type_)
    thread_tablename = get_history_thread_table_name(feature.type_)
    usage_file = (
        get_sqlite_usage_file(feature.id_)
        if feature.type_ != OrganisationFeatureType.ASK_PUBLIC
        else get_public_sqlite_usage_file(str(feature.id_))
    )
    with closing(sqlite3.connect(usage_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(
        connection.cursor()
    ) as cursor:
        cursor.execute(
            SQL_CREATE_MESSAGE_TABLE.format(
                table=tablename,
                thread_table=thread_tablename,
            )
        )

        for x in data:
            log.debug("Saving message: %s", x)
            cursor.execute(f"INSERT INTO {tablename} (message, human, timestamp, thread_id) VALUES (?, ?, ?, ?)", x)  # noqa: S608
            rows.append((cursor.lastrowid, x[0], x[1], x[2], x[3]))
        connection.commit()

    return rows


def _retrieve_messages(
    cutoff: datetime, size: int, feature: FeatureKey, thread_id: int, sort_order: Literal["ASC", "DESC"] = "DESC"
) -> list[tuple[int, str, bool, datetime, int]]:
    """Retrieve the history of messages up to certain size and cutoff.

    Args:
        cutoff: The cutoff time.
        size: The number of messages to retrieve.
        feature: The feature key.
        thread_id: The thread id.
        sort_order: The order to sort the messages.

    Returns:
        list pf tuples of (id:int, message:str, human:bool, timestamp, thread_id:int).
    """
    tablename = get_history_table_name(feature.type_)
    thread_tablename = get_history_thread_table_name(feature.type_)
    usage_file = (
        get_sqlite_usage_file(feature.id_)
        if feature.type_ != OrganisationFeatureType.ASK_PUBLIC
        else get_public_sqlite_usage_file(str(feature.id_))
    )
    rows = None
    with closing(sqlite3.connect(usage_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(
        connection.cursor()
    ) as cursor:
        cursor.execute(SQL_CREATE_THREAD_TABLE.format(table=thread_tablename))
        cursor.execute(SQL_CREATE_MESSAGE_TABLE.format(table=tablename, thread_table=thread_tablename))
        log.debug("Retrieving message params: thread_id=%s, cutoff=%s, size=%s", thread_id, cutoff, size)
        if sort_order == "ASC":
            rows = cursor.execute(
                f"SELECT id, message, human, timestamp, thread_id FROM {tablename} WHERE thread_id = ? AND timestamp < ? ORDER BY timestamp LIMIT ?",  # noqa: S608
                (thread_id, cutoff, size),
            ).fetchall()
        else:
            rows = cursor.execute(
                f"SELECT id, message, human, timestamp, thread_id FROM {tablename} WHERE thread_id = ? AND timestamp < ? ORDER BY timestamp DESC LIMIT ?",  # noqa: S608
                (thread_id, cutoff, size),
            ).fetchall()
            rows.reverse()

    return rows


def list_thread_history(feature: FeatureKey, id_: Optional[int] = None) -> list[tuple[int, str, int]]:
    """List the history messages for the thread."""
    tablename = get_history_thread_table_name(feature.type_)
    rows = None
    with closing(
        sqlite3.connect(get_sqlite_usage_file(feature.id_), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            SQL_CREATE_THREAD_TABLE.format(
                table=tablename,
            )
        )
        if id_:
            rows = cursor.execute(f"SELECT id, topic, created_at FROM {tablename} WHERE id = ?", (id_,)).fetchall()  # noqa: S608
        else:
            # FIXME: this returns all the messages across all threads which doesn't make sense. This method should be refactored to get_thread_history with thread_id param being required.
            rows = cursor.execute(f"SELECT id, topic, created_at FROM {tablename} ORDER BY created_at DESC").fetchall()  # noqa: S608

    return rows


def get_thread_topic(feature: FeatureKey, thread_id: int) -> str | None:
    """Retrieve the topic of a thread."""
    tablename = get_history_thread_table_name(feature.type_)
    row = None
    with closing(
        sqlite3.connect(get_sqlite_usage_file(feature.id_), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            SQL_CREATE_THREAD_TABLE.format(
                table=tablename,
            )
        )
        row = cursor.execute(f"SELECT topic FROM {tablename} WHERE id = ?", (thread_id,)).fetchone()  # noqa: S608

    return row[0] if row else None  # f"New thread {thread_id}"


def update_thread_topic(topic: str, feature: FeatureKey, thread_id: int) -> None:
    """Update the topic of a thread."""
    tablename = get_history_thread_table_name(feature.type_)
    with closing(
        sqlite3.connect(get_sqlite_usage_file(feature.id_), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            SQL_CREATE_THREAD_TABLE.format(
                table=tablename,
            )
        )
        cursor.execute(f"UPDATE {tablename} SET topic = ? WHERE id = ?", (topic, thread_id))  # noqa: S608
        connection.commit()


def get_chat_summerised_history(
    feature: FeatureKey, thread_id: int, size: Optional[int] = None
) -> list[tuple[int, str, bool]]:
    """Retrieve the top messages for a chat thread."""
    if size is None:
        size = NUMBER_OF_MESSAGES_IN_HISTORY
    return [(x[:3]) for x in _retrieve_messages(datetime.now(), size, feature, thread_id, sort_order="ASC")]


def _retrieve_last_n_history(feature: FeatureKey, thread_id: int) -> str:
    return ("\n").join(
        map(
            lambda row: f"{'Human' if row[2] else 'Assistant'}: {row[1]}",
            _retrieve_messages(datetime.now(), NUMBER_OF_MESSAGES_IN_HISTORY, feature, thread_id),
        )
    )


def get_history_as_chat_messages(
    feature: FeatureKey, thread_id: int, size: Optional[int] = NUMBER_OF_MESSAGES_IN_HISTORY
) -> list[ChatMessage]:
    """Retrieve the history of as LlamaIndex ChatMessage objects."""
    result = _retrieve_messages(datetime.now(), NUMBER_OF_MESSAGES_IN_HISTORY, feature, thread_id)
    # id, message, human, timestamp, thread_id
    history_chat_message = [
        ChatMessage(role=(MessageRole.USER if x[2] else MessageRole.ASSISTANT), content=x[1]) for x in result
    ]

    return history_chat_message


def create_history_thread(topic: str, feature: FeatureKey) -> int | None:
    """Create a new thread for the history i.e a new chat session."""
    tablename = get_history_thread_table_name(feature.type_)
    with closing(
        sqlite3.connect(get_sqlite_usage_file(feature.id_), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            SQL_CREATE_THREAD_TABLE.format(
                table=tablename,
            )
        )

        cursor.execute(f"INSERT INTO {tablename} (topic) VALUES (?)", (topic,))  # noqa: S608

        id_ = cursor.lastrowid
        connection.commit()

    return id_

def delete_thread(thread_id: int, feature: FeatureKey) -> bool:
    """Delete a thread and its associated messages.

    feature.id_ needs to be the user_id.
    """
    thread_tablename = get_history_thread_table_name(feature.type_)
    message_tablename = get_history_table_name(feature.type_)
    usage_file = (
        get_sqlite_usage_file(feature.id_)
        if feature.type_ != OrganisationFeatureType.ASK_PUBLIC
        else get_public_sqlite_usage_file(str(feature.id_))
    )
    is_deleted = False
    with closing(sqlite3.connect(usage_file, detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(
        connection.cursor()
    ) as cursor:
        cursor.execute("PRAGMA foreign_keys = ON;")
        try:
            cursor.execute(f"DELETE FROM {message_tablename} WHERE thread_id = ?", (thread_id,))  # noqa: S608
            cursor.execute(f"DELETE FROM {thread_tablename} WHERE id = ?", (thread_id,))  # noqa: S608
            connection.commit()
            is_deleted = True
        except sqlite3.Error as e:
            connection.rollback()
            # raise e
            is_deleted = False
    return is_deleted


def get_latest_thread(feature: FeatureKey) -> tuple[int, str, int] | None:
    """Retrieve the most recently created thread.

    Use the id (thread_id) to retrieve the history of messages.

    Returns:
        (id, topic, created_at). The id is the thread_id.
    """
    tablename = get_history_thread_table_name(feature.type_)
    rows = None
    with closing(
        sqlite3.connect(get_sqlite_usage_file(feature.id_), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            SQL_CREATE_THREAD_TABLE.format(
                table=tablename,
            )
        )
        rows = cursor.execute(
            f"SELECT id, topic, created_at FROM {tablename} ORDER BY created_at DESC LIMIT 1"  # noqa: S608
        ).fetchall()
        rows.reverse()

    return rows[0] if rows else None


def thread_exists(thread_id: int, user_id: int, feature_type: OrganisationFeatureType) -> bool:
    """Check if a thread exists."""
    thread_exists = False
    tablename = get_history_thread_table_name(feature_type)
    try:
        with closing(
            sqlite3.connect(get_sqlite_usage_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
        ) as connection, closing(connection.cursor()) as cursor:
            row = cursor.execute(f"SELECT id FROM {tablename} WHERE id = ?", (thread_id,)).fetchone()  # noqa: S608
            thread_exists = row is not None
    except Exception:
        thread_exists = False

    return thread_exists


def query(
    input_: str,
    feature: FeatureKey,
    thread_id: int,
    model_settings_collection: LlmUsageSettingsCollection,
    assistant: Assistant,
    spaces: Optional[list[SpaceKey]] = None,
) -> list:
    """Run the query again documents in the space(s) using a LLM."""
    log.debug(
        "Query: '%s' for feature: '%s' with shared-spaces: '%s'",
        input_,
        feature,
        spaces,
    )
    data = [(input_, bool(True), datetime.now(), thread_id)]
    is_chat = feature.type_ == OrganisationFeatureType.CHAT_PRIVATE

    # history = _retrieve_last_n_history(feature, thread_id)

    history_messages = get_history_as_chat_messages(feature=feature, thread_id=thread_id)

    log.debug("is_chat: %s", is_chat)
    try:
        response = (
            run_chat(input_, history_messages, model_settings_collection, assistant)
            if is_chat
            else run_ask(input_, history_messages, model_settings_collection, assistant, spaces)
        )
        log.debug("Response: %s", response)

    except Exception as e:
        response = query_error(e, model_settings_collection)

    log.debug("thread_id: %s", thread_id)
    data.append(
        (
            MESSAGE_TEMPLATE.format(message=response.response)
            if is_chat
            else MESSAGE_WITH_SOURCES_TEMPLATE.format(
                message=response, source=format_document_sources(response.source_nodes)
            ),
            False,
            datetime.now(),
            thread_id,
        )
    )

    return _save_messages(data, feature)


def history(
    cutoff: datetime, size: int, feature: FeatureKey, thread_id: int
) -> list[tuple[int, str, bool, datetime, int]]:
    """Retrieve the history of messages up to certain size and cutoff."""
    return _retrieve_messages(cutoff, size, feature, thread_id)
