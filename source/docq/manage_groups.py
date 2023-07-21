"""Functions to manage user groups."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Tuple

from .support.store import get_sqlite_system_file

SQL_CREATE_GROUPS_TABLE = """
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SQL_CREATE_MEMBERSHIPS_TABLE = """
CREATE TABLE IF NOT EXISTS memberships (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    PRIMARY KEY (group_id, user_id)
)
"""


def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_GROUPS_TABLE)
        cursor.execute(SQL_CREATE_MEMBERSHIPS_TABLE)
        connection.commit()


def list_groups(
    name_match: str = None,
) -> list[Tuple[int, str, List[Tuple[int, str]], datetime, datetime]]:
    """List groups.

    Args:
        name_match (str, optional): The group name match. Defaults to None.

    Returns:
        list[tuple[int, str, datetime, datetime]]: The list of groups.
    """
    log.debug("Listing groups: %s", name_match)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        groups = cursor.execute(
            "SELECT id, name, created_at, updated_at FROM groups WHERE name LIKE ?",
            (f"%{name_match}%" if name_match else "%",),
        ).fetchall()

        memberships = cursor.execute(
            "SELECT m.group_id, u.id, u.fullname from memberships m, users u WHERE m.group_id IN ({}) AND m.user_id = u.id".format(  # noqa: S608
                ",".join([str(x[0]) for x in groups])
            )
        ).fetchall()

        return [(x[0], x[1], [(y[1], y[2]) for y in memberships if y[0] == x[0]], x[2], x[3]) for x in groups]


def create_group(name: str) -> bool:
    """Create a group.

    Args:
        name (str): The group name.

    Returns:
        bool: True if the group is created, False otherwise.
    """
    log.debug("Creating group: %s", name)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO groups (name) VALUES (?)",
            (name,),
        )
        connection.commit()
        return True


def update_group(id_: int, members: List[int], name: str = None) -> bool:
    """Update a group.

    Args:
        id_ (int): The group id.
        members (list[int], optional): The members. Defaults to None.
        name (str, optional): The group name. Defaults to None.

    Returns:
        bool: True if the group is updated, False otherwise.
    """
    log.debug("Updating group: %d", id_)

    query = "UPDATE groups SET updated_at = ?"
    params = [
        datetime.now(),
    ]

    if name:
        query += ", name = ?"
        params.append(name)

    query += " WHERE id = ?"
    params.append(id_)

    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(query, params)
        cursor.execute("DELETE FROM memberships WHERE group_id = ?", (id_,))
        cursor.executemany("INSERT INTO memberships (group_id, user_id) VALUES (?, ?)", [(id_, x) for x in members])
        connection.commit()
        return True


def delete_group(id_: int) -> bool:
    """Delete a group.

    Args:
        id_ (int): The group id.

    Returns:
        bool: True if the group is deleted, False otherwise.
    """
    log.debug("Deleting group: %d", id_)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("DELETE FROM groups WHERE id = ?", (id_,))
        connection.commit()
        return True
