"""Functions to manage orgs."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Tuple

from .support.store import get_sqlite_system_file

SQL_CREATE_ORGS_TABLE = """
CREATE TABLE IF NOT EXISTS orgs (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    archived BOOL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SQL_CREATE_ORG_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS org_members (
    org_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (org_id) REFERENCES orgs (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    PRIMARY KEY (org_id, user_id)
)
"""

# organisations

DEFAULT_ORG_ID = 1000
DEFAULT_ORG_NAME = "Docq Org"


def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_ORGS_TABLE)
        cursor.execute(SQL_CREATE_ORG_MEMBERS_TABLE)
        connection.commit()


def _init_default_org_if_necessary() -> bool:
    created = False
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        (count,) = cursor.execute("SELECT COUNT(*) FROM orgs WHERE id = ?", (DEFAULT_ORG_ID,)).fetchone()
        if int(count) > 0:
            log.debug("Default org found, skipping creation...", count)
            return False
        else:
            log.info("No default org found, creating one with default values...")

            cursor.execute(
                "INSERT INTO orgs (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (DEFAULT_ORG_ID, DEFAULT_ORG_NAME, datetime.now(), datetime.now()),
            )
            connection.commit()
            created = True

    return created


def list_organisations(
    name_match: str = None, user_id: int = None
) -> List[Tuple[int, str, List[Tuple[int, str]], datetime, datetime]]:
    """List orgs.

    Args:
        name_match (str, optional): The org name to match. Defaults to None.
        user_id (int, optional): The user id. Defaults to None.

    Returns:
        List[Tuple[int, str, List[Tuple[int, str]], datetime, datetime]]: The list of orgs [org_id, org_name, [user id, users fullname] created_at, updated_at].
    """
    log.debug("Listing orgs: %s", name_match)
    orgs = []
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        if user_id:
            orgs = cursor.execute(
                "SELECT id, name, created_at, updated_at FROM orgs WHERE name LIKE ?",
                (f"%{name_match}%" if name_match else "%",),
            ).fetchall()
        else:
            orgs = cursor.execute(
                "SELECT o.id, o.name, o.created_at, o.updated_at FROM orgs o LEFT JOIN org_members om ON user_id = ? AND o.id = om.org_id",
                (user_id,),
            ).fetchall()

        members = cursor.execute(
            "SELECT m.org_id, u.id, u.fullname from org_members m, users u WHERE m.org_id IN ({}) AND m.user_id = u.id".format(  # noqa: S608
                ",".join([str(x[0]) for x in orgs])
            )
        ).fetchall()

        return [(x[0], x[1], [(y[1], y[2]) for y in members if y[0] == x[0]], x[2], x[3]) for x in orgs]
        # return orgs


def add_organisation_member(org_id: int, user_id: int) -> bool:
    """Add a user to an org as a member."""
    log.debug("Adding user: %s to org: %s", user_id, org_id)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO org_members (org_id, user_id) VALUES (?, ?)",
            (org_id, user_id),
        )
        connection.commit()
        return True


def update_organisation_members(org_id: int, user_ids: List[int]) -> bool:
    """Update org members.

    Args:
        org_id (int): The org id.
        user_ids (List[int]): The user ids.

    Returns:
        bool: True if the org members are updated, False otherwise.
    """
    log.debug("Updating org members for org_id: %s", org_id)
    success = False
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(
                "DELETE FROM org_members WHERE org_id = ?",
                (org_id,),
            )
            cursor.executemany(
                "INSERT INTO org_members (org_id, user_id) VALUES (?, ?)", [(org_id, x) for x in user_ids]
            )
            connection.commit()
            success = True
        except Exception as e:
            success = False
            connection.rollback()
            log.error("Error updating org members, rolled back: %s", e)

    return success


def create_organisation(name: str, creating_user_id: int) -> bool:
    """Create an org.

    Args:
        name (str): The org name.
        creating_user_id (int): The user id of the user creating the org.

    Returns:
        bool: True if the org is created, False otherwise.
    """
    success = False
    log.debug("Creating org: %s", name)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(
                "INSERT INTO orgs (name) VALUES (?)",
                (name,),
            )
            org_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO org_members (org_id, user_id) VALUES (?, ?)",
                (org_id, creating_user_id),
            )
            connection.commit()
            success = True
            log.info("Created organization %s with member %s", org_id, creating_user_id)
        except Exception as e:
            # Rollback transaction on error
            success = False
            connection.rollback()
            log.error("Error creating organization with member, rolled back: %s", e)

        return success


def update_organisation(id_: int, name: str = None) -> bool:
    """Update a group.

    Args:
        id_ (int): The group id.
        name (str, optional): The group name. Defaults to None.

    Returns:
        bool: True if the orgs is updated, False otherwise.
    """
    log.debug("Updating orgs: %d", id_)

    query = "UPDATE orgs SET updated_at = ?"
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
        return True


def archive_organisation(id_: int) -> bool:
    """Archive a org.

    Args:
        id_ (int): The org id.

    Returns:
        bool: True if the org is archived, False otherwise.
    """
    log.debug("Archiving user: %d", id_)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "UPDATE orgs SET archived = 1, updated_at = ? WHERE id = ?",
            (
                datetime.now(),
                id_,
            ),
        )
        connection.commit()
        return True
