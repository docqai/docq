"""Functions to run queries."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime

from .config import FeatureType
from .domain import FeatureKey, SpaceKey
from .support.llm import run_ask, run_chat, query_error
from .support.store import get_history_table_name, get_sqlite_usage_file
from .manage_documents import format_document_sources

SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS {table} (
    id INTEGER PRIMARY KEY,
    message TEXT,
    human BOOL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

MESSAGE_TEMPLATE = "{message}"

MESSAGE_WITH_SOURCES_TEMPLATE = "{message}\n\nSource(s):\n{source}"

NUMBER_OF_MESSAGES_IN_HISTORY = 10


def _save_messages(data: list[tuple[str, bool, datetime]], feature: FeatureKey) -> list[int]:
    rows = []
    tablename = get_history_table_name(feature.type_)
    with closing(
        sqlite3.connect(get_sqlite_usage_file(feature.id_), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            SQL_CREATE_TABLE.format(
                table=tablename,
            )
        )

        for x in data:
            cursor.execute(f"INSERT INTO {tablename} (message, human, timestamp) VALUES (?, ?, ?)", x)
            rows.append((cursor.lastrowid, x[0], x[1], x[2]))
        connection.commit()

    return rows


def _retrieve_messages(cutoff: datetime, size: int, feature: FeatureKey) -> list[tuple[int, str, bool, datetime]]:
    tablename = get_history_table_name(feature.type_)
    rows = None
    with closing(
        sqlite3.connect(get_sqlite_usage_file(feature.id_), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            SQL_CREATE_TABLE.format(
                table=tablename,
            )
        )
        rows = cursor.execute(
            f"SELECT id, message, human, timestamp FROM {tablename} WHERE timestamp < ? ORDER BY timestamp LIMIT ?",
            (
                cutoff,
                size,
            ),
        ).fetchall()

    return rows


def _retrieve_last_n_history(feature: FeatureKey) -> str:
    return ("\n").join(
        map(
            lambda row: f"{'Human' if row[2] else 'Assistant'}: {row[1]}",
            _retrieve_messages(datetime.now(), NUMBER_OF_MESSAGES_IN_HISTORY, feature),
        )
    )


def query(input_: str, feature: FeatureKey, space: SpaceKey, spaces: list[SpaceKey] = None) -> list[int]:
    """Run the query again documents in the space(s) using a LLM."""
    log.debug("Query: %s for %s with p-space %s and s-spaces %s", input_, feature, space, spaces)
    data = [(input_, True, datetime.now())]
    is_chat = feature.type_ == FeatureType.CHAT_PRIVATE

    history = _retrieve_last_n_history(feature)

    try:
        response = run_chat(input_, history) if is_chat else run_ask(input_, history, space, spaces)
        log.debug("Response: %s", response)

    except Exception as e: response = query_error(e)

    data.append(
        (
            MESSAGE_TEMPLATE.format(message=response.response)
            if is_chat
            else MESSAGE_WITH_SOURCES_TEMPLATE.format(
                message=response.response, source=format_document_sources(response.source_nodes, space)
            ),
            False,
            datetime.now(),
        )
    )

    return _save_messages(data, feature)


def history(cutoff: datetime, size: int, feature: FeatureKey) -> list[tuple[int, str, bool, datetime]]:
    """Retrieve the history of messages up to certain size and cutoff."""
    return _retrieve_messages(cutoff, size, feature)
