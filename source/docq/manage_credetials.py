"""Manage Credentials."""

import json
import sqlite3
from contextlib import closing
from typing import Optional

from .support.store import get_sqlite_system_file

SQL_CREATE_CREDENTIALS_TABLE = """
CREATE TABLE IF NOT EXISTS credentials (
    org_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    key TEXT,
    val TEXT,
    FOREIGN KEY (org_id) REFERENCES orgs (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    PRIMARY KEY (org_id, user_id, key)
)
"""

def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_CREDENTIALS_TABLE)
        connection.commit()


def get_credential(org_id: int, user_id: int, key: str) -> Optional[dict]:
    """Get the user credential for the given key."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT val FROM credentials WHERE key = ? AND org_id = ? AND user_id = ?",
            (key, org_id, user_id),
        )
        row = cursor.fetchone()
        return json.loads(row[0]) if row else None


def set_credential(org_id: int, user_id: int, key: str, val: str) -> None:
    """Set the user credential for the given key."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT OR REPLACE INTO credentials (key, org_id, user_id, val) VALUES (?, ?, ?, ?)",
            (key, org_id, user_id, val),
        )
        connection.commit()


def remove_credential(org_id: int, user_id: int, key: str) -> None:
    """Delete the user credential for the given key."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "DELETE FROM credentials WHERE key = ? AND org_id = ? AND user_id = ?",
            (key, org_id, user_id),
        )
        connection.commit()
