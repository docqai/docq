"""Functions to manage user groups."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Tuple

from .support.store import get_sqlite_shared_system_file

SQL_CREATE_USER_GROUPS_TABLE = """
CREATE TABLE IF NOT EXISTS user_groups (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    org_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES orgs (id)
)
"""

SQL_CREATE_USER_GROUP_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS user_group_members (
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES user_groups (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    PRIMARY KEY (group_id, user_id)
)
"""


def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_USER_GROUPS_TABLE)
        cursor.execute(SQL_CREATE_USER_GROUP_MEMBERS_TABLE)
        connection.commit()


def list_user_groups(
    org_id: int,
    name_match: str = None,
) -> List[Tuple[int, str, List[Tuple[int, str]], datetime, datetime]]:
    """List user groups.

    Args:
        org_id (int): The org id.
        name_match (str, optional): The group name match. Defaults to None.

    Returns:
        List[Tuple[int, str, List[Tuple[int, str]], datetime, datetime]]: The list of user groups.
    """
    log.debug("Listing user groups that match: '%s' for org_id: %s", name_match, org_id)
    if not org_id:
        raise ValueError("`org_id` cannot be None.")

    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        user_groups = cursor.execute(
            "SELECT id, name, created_at, updated_at FROM user_groups WHERE org_id = ? AND name LIKE ?",
            (
                org_id,
                f"%{name_match}%" if name_match else "%",
            ),
        ).fetchall()

        members = cursor.execute(
            "SELECT m.group_id, u.id, u.fullname FROM user_group_members m, users u WHERE m.group_id IN ({}) AND m.user_id = u.id".format(  # noqa: S608
                ",".join([str(x[0]) for x in user_groups])
            )
        ).fetchall()

        return [(x[0], x[1], [(y[1], y[2]) for y in members if y[0] == x[0]], x[2], x[3]) for x in user_groups]


def create_user_group(name: str, org_id: int) -> bool:
    """Create a user group.

    Args:
        name (str): The group name.
        org_id (int): The org id.

    Returns:
        bool: True if the user group is created, False otherwise.
    """
    log.debug("Creating user group: %s", name)
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO user_groups (name, org_id) VALUES (?, ?)",
            (name, org_id),
        )
        connection.commit()
        return True


def update_user_group(id_: int, members: List[int], name: str = None) -> bool:
    """Update a group.

    Args:
        id_ (int): The group id.
        members (List[int]): The members.
        name (str, optional): The group name. Defaults to None.

    Returns:
        bool: True if the user group is updated, False otherwise.
    """
    log.debug("Updating user group: %d", id_)

    query = "UPDATE user_groups SET updated_at = ?"
    params = [
        datetime.now(),
    ]

    if name:
        query += ", name = ?"
        params.append(name)

    query += " WHERE id = ?"
    params.append(id_)

    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(query, params)
        cursor.execute("DELETE FROM user_group_members WHERE group_id = ?", (id_,))
        cursor.executemany(
            "INSERT INTO user_group_members (group_id, user_id) VALUES (?, ?)", [(id_, x) for x in members]
        )
        connection.commit()
        return True


def delete_user_group(id_: int, org_id: int) -> bool:
    """Delete a user group.

    Args:
        id_ (int): The user group id.
        org_id (int): The org id the group belongs to.

    Returns:
        bool: True if the user group is deleted, False otherwise.
    """
    log.debug("Deleting user group: %d", id_)
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("DELETE FROM user_group_members WHERE group_id = ? ", (id_,))
        cursor.execute("DELETE FROM user_groups WHERE id = ? AND org_id = ?", (id_, org_id))
        connection.commit()
        return True
