"""Functions to run queries."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime

from .config import FeatureType
from .domain import FeatureKey, SpaceKey
from .manage_documents import format_document_sources
from .support.llm import query_error, run_ask, run_chat
from .support.store import (
    get_history_table_name,
    get_history_thread_table_name,
    get_public_sqlite_usage_file,
    get_sqlite_usage_file,
)

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


def _save_messages(data: list[tuple[str, bool, datetime, int]], feature: FeatureKey) -> list[int]:
    rows = []
    tablename = get_history_table_name(feature.type_)
    thread_tablename = get_history_thread_table_name(feature.type_)
    usage_file = get_sqlite_usage_file(feature.id_) if feature.type_ != FeatureType.ASK_PUBLIC else get_public_sqlite_usage_file(feature.id_)
    with closing(
        sqlite3.connect(usage_file, detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            SQL_CREATE_MESSAGE_TABLE.format(
                table=tablename,
                thread_table=thread_tablename,
            )
        )

        for x in data:
            log.debug("Saving message: %s", x)
            cursor.execute(f"INSERT INTO {tablename} (message, human, timestamp, thread_id) VALUES (?, ?, ?, ?)", x)
            rows.append((cursor.lastrowid, x[0], x[1], x[2], x[3]))
        connection.commit()

    return rows


def _retrieve_messages(
    cutoff: datetime, size: int, feature: FeatureKey, thread_id: int
) -> list[tuple[int, str, bool, datetime, int]]:
    tablename = get_history_table_name(feature.type_)
    thread_tablename = get_history_thread_table_name(feature.type_)
    usage_file = get_sqlite_usage_file(feature.id_) if feature.type_ != FeatureType.ASK_PUBLIC else get_public_sqlite_usage_file(feature.id_)
    rows = None
    with closing(
        sqlite3.connect(usage_file, detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_THREAD_TABLE.format(table=thread_tablename))
        cursor.execute(SQL_CREATE_MESSAGE_TABLE.format(table=tablename, thread_table=thread_tablename))
        log.debug("Retrieving message params: thread_id=%s, cutoff=%s, size=%s", thread_id, cutoff, size)
        rows = cursor.execute(
            f"SELECT id, message, human, timestamp, thread_id FROM {tablename} WHERE thread_id = ? AND timestamp < ? ORDER BY timestamp DESC LIMIT ?",
            (thread_id, cutoff, size),
        ).fetchall()
        rows.reverse()

    return rows


def _retrieve_last_n_history(feature: FeatureKey, thread_id: int) -> str:
    return ("\n").join(
        map(
            lambda row: f"{'Human' if row[2] else 'Assistant'}: {row[1]}",
            _retrieve_messages(datetime.now(), NUMBER_OF_MESSAGES_IN_HISTORY, feature, thread_id),
        )
    )


def create_history_thread(topic: str, feature: FeatureKey) -> int:
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

        cursor.execute(f"INSERT INTO {tablename} (topic) VALUES (?)", (topic,))

        id_ = cursor.lastrowid
        connection.commit()

    return id_


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
            f"SELECT id, topic, created_at FROM {tablename} ORDER BY created_at DESC LIMIT 1"
        ).fetchall()
        rows.reverse()

    return rows[0] if rows else None


def query(
    input_: str, feature: FeatureKey, thread_id: int, space: SpaceKey = None, spaces: list[SpaceKey] = None
) -> list[int]:
    """Run the query again documents in the space(s) using a LLM."""
    log.debug(
        "Query: '%s' for feature: '%s' with personal-space: '%s' and shared-spaces: '%s'",
        input_,
        feature,
        space,
        spaces,
    )
    data = [(input_, True, datetime.now(), thread_id)]
    is_chat = feature.type_ == FeatureType.CHAT_PRIVATE

    history = _retrieve_last_n_history(feature, thread_id)

    try:
        response = run_chat(input_, history) if is_chat else run_ask(input_, history, space, spaces)
        log.debug("Response: %s", response)

    except Exception as e:
        response = query_error(e)

    log.debug("thread_id: %s", thread_id)
    data.append(
        (
            MESSAGE_TEMPLATE.format(message=response.response)
            if is_chat
            else MESSAGE_WITH_SOURCES_TEMPLATE.format(
                message=response.response, source=format_document_sources(response.source_nodes)
            ),
            False,
            datetime.now(),
            thread_id,
        )
    )

    return _save_messages(data, feature)


def history(cutoff: datetime, size: int, feature: FeatureKey, thread_id: int) -> list[tuple[int, str, bool, datetime]]:
    """Retrieve the history of messages up to certain size and cutoff."""
    return _retrieve_messages(cutoff, size, feature, thread_id)
