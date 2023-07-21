"""Functions to manage engagements."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Tuple

from .support.store import get_sqlite_system_file

SQL_CREATE_ENGAGEMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS engagements (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SQL_CREATE_COMPOSITIONS_TABLE = """
CREATE TABLE IF NOT EXISTS compositions (
    engagement_id INTEGER NOT NULL,
    space_id INTEGER NOT NULL,
    FOREIGN KEY (engagement_id) REFERENCES engagements (id) ON DELETE CASCADE,
    FOREIGN KEY (space_id) REFERENCES spaces (id),
    UNIQUE (engagement_id, space_id)
)
"""


def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_ENGAGEMENTS_TABLE)
        cursor.execute(SQL_CREATE_COMPOSITIONS_TABLE)
        connection.commit()


def list_engagements(name_match: str = None) -> list[Tuple[int, str, List[Tuple[int, str]], datetime, datetime]]:
    """List groups.

    Args:
        name_match (str, optional): The engagement name match. Defaults to None.

    Returns:
        list[tuple[int, str, datetime, datetime]]: The list of groups.
    """
    log.debug("Listing engagements: %s", name_match)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        engagements = cursor.execute(
            "SELECT id, name, summary, created_at, updated_at FROM engagements WHERE name LIKE ?",
            (f"%{name_match}%" if name_match else "%",),
        ).fetchall()

        compositions = cursor.execute(
            "SELECT c.engagement_id, s.id, s.name from spaces s, compositions c WHERE c.engagement_id in ({}) AND c.space_id = s.id".format(  # noqa: S608
                ",".join([str(x[0]) for x in engagements])
            )
        ).fetchall()

        return [
            (x[0], x[1], x[2], [(y[1], y[2]) for y in compositions if y[0] == x[0]], x[3], x[4]) for x in engagements
        ]


def create_engagement(name: str, summary: str = None) -> bool:
    """Create a engagement.

    Args:
        name (str): The engagement name.
        summary (str, optional): The engagement summary. Defaults to None.

    Returns:
        bool: True if the engagement is created, False otherwise.
    """
    log.debug("Creating engagement: %s", name)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO engagements (name, summary) VALUES (?, ?)",
            (
                name,
                summary,
            ),
        )
        connection.commit()
        return True


def update_engagement(id_: int, associations: List[int], name: str = None, summary: str = None) -> bool:
    """Update a group.

    Args:
        id_ (int): The group id.
        associations (List[int]): The list of space ids.
        name (str, optional): The group name. Defaults to None.
        summary (str, optional): The group summary. Defaults to None.

    Returns:
        bool: True if the group is updated, False otherwise.
    """
    log.debug("Updating engagement: %d", id_)

    query = "UPDATE engagements SET updated_at = ?"
    params = [
        datetime.now(),
    ]

    if name:
        query += ", name = ?"
        params.append(name)

    if summary:
        query += ", summary = ?"
        params.append(summary)

    query += " WHERE id = ?"
    params.append(id_)

    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(query, params)
        cursor.execute("DELETE FROM compositions WHERE engagement_id = ?", (id_,))
        cursor.executemany(
            "INSERT INTO compositions (engagement_id, space_id) VALUES (?, ?)", [(id_, x) for x in associations]
        )
        connection.commit()
        return True


def delete_engagement(id_: int) -> bool:
    """Delete an engagement.

    Args:
        id_ (int): The engagement id.

    Returns:
        bool: True if the engagement is deleted, False otherwise.
    """
    log.debug("Deleting group: %d", id_)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("DELETE FROM engagements WHERE id = ?", (id_,))
        connection.commit()
        return True
