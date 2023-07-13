"""Functions to manage groups."""

import json
import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Optional

from .support.store import get_sqlite_system_file

SQL_CREATE_GROUPS_TABLE = """
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    members TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def list_groups(groupname_match: Optional[str] = None) -> list[tuple[int, str, List[int], datetime, datetime]]:
    """List groups.

    Args:
        groupname_match (str, optional): The group name match. Defaults to None.

    Returns:
        list[tuple[int, str, datetime, datetime]]: The list of groups.
    """
    log.debug("Listing groups: %s", groupname_match)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_GROUPS_TABLE)
        rows = cursor.execute(
            "SELECT id, name, members, created_at, updated_at FROM groups WHERE name LIKE ?",
            (f"%{groupname_match}%" if groupname_match else "%",),
        ).fetchall()

        return [(x[0], x[1], json.loads(x[2]) if x[2] else [], x[3], x[4]) for x in rows]


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
        cursor.execute(SQL_CREATE_GROUPS_TABLE)
        cursor.execute(
            "INSERT INTO groups (name) VALUES (?)",
            (name,),
        )
        connection.commit()
        return True


def update_group(id_: int, members: List[int], name: Optional[str] = None) -> bool:
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

    query += ", members = ?"
    params.append(json.dumps(members))

    if name:
        query += ", name = ?"
        params.append(name)

    query += " WHERE id = ?"
    params.append(id_)

    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_GROUPS_TABLE)
        cursor.execute(query, params)
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
        cursor.execute(SQL_CREATE_GROUPS_TABLE)
        cursor.execute("DELETE FROM groups WHERE id = ?", (id_,))
        connection.commit()
        return True
