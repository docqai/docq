"""Functions to manage spaces."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime

from .config import SpaceType
from .domain import SpaceKey
from .support.llm import reindex
from .support.store import get_sqlite_system_file

SQL_CREATE_SPACES_TABLE = """
CREATE TABLE IF NOT EXISTS space (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    summary TEXT,
    archived BOOL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def get_shared_space(id_: int) -> tuple[int, str, str, bool, datetime, datetime]:
    """Get a shared space."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SPACES_TABLE)
        cursor.execute("SELECT id, name, summary, archived, created_at, updated_at FROM space WHERE id = ?", (id_,))
        return cursor.fetchone()


def update_shared_space(id_: int, name: str = None, summary: str = None, archived: bool = False) -> bool:
    """Update a shared space."""
    query = "UPDATE space SET updated_at = ?"
    params = (datetime.now(),)

    if name:
        query += ", name = ?"
        params += (name,)
    if summary:
        query += ", summary = ?"
        params += (summary,)

    query += ", archived = ?"
    params += (archived,)

    query += " WHERE id = ?"
    params += (id_,)

    log.debug("Updating space %d with query: %s | Params: %s", id_, query, params)

    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(query, params)
        connection.commit()
        log.debug("Updated space %d", id_)
        return True


def create_shared_space(name: str, summary: str) -> int:
    """Create a shared space."""
    params = (
        name,
        summary,
    )
    log.debug("Creating space with params: %s", params)
    rowid = None
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SPACES_TABLE)
        cursor.execute("INSERT INTO space (name, summary) VALUES (?, ?)", params)
        rowid = cursor.lastrowid
        connection.commit()
        log.debug("Created space with rowid: %d", rowid)

    reindex(SpaceKey(SpaceType.SHARED, rowid))

    return rowid


def list_shared_spaces() -> list[tuple[int, str, str, bool, datetime, datetime]]:
    """List all shared spaces."""
    rows = []
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SPACES_TABLE)
        rows = cursor.execute(
            "SELECT id, name, summary, archived, created_at, updated_at FROM space ORDER BY name"
        ).fetchall()
    return rows
