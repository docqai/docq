"""Functions to manage orgs."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Tuple

from . import manage_settings, manage_users
from .constants import DEFAULT_ORG_ID, DEFAULT_ORG_NAME
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

def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_ORGS_TABLE)
        connection.commit()


def _init_default_org_if_necessary() -> bool:
    created = False
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        (count,) = cursor.execute("SELECT COUNT(*) FROM orgs WHERE id = ?", (DEFAULT_ORG_ID,)).fetchone()
        if int(count) > 0:
            log.debug("Default org found, skipping creation...")
            return False
        else:
            log.info("No default org found, creating one with default values...")

            cursor.execute(
                "INSERT INTO orgs (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (DEFAULT_ORG_ID, DEFAULT_ORG_NAME, datetime.now(), datetime.now()),
            )
            connection.commit()
            manage_settings._init_default_system_settings()
            manage_settings._init_default_org_settings(DEFAULT_ORG_ID)
            created = True

    return created


def list_organisations(
    name_match: str = None, user_id: int = None
) -> List[Tuple[int, str, List[Tuple[int, str, bool]], datetime, datetime]]:
    """List orgs.

    Args:
        name_match (str, optional): The org name to match. Defaults to None.
        user_id (int, optional): The user id. Defaults to None.

    Returns:
        List[Tuple[int, str, List[Tuple[int, str, bool]], datetime, datetime]]: The list of orgs [org_id, org_name, [user id, users fullname, is org admin] created_at, updated_at].
    """
    orgs = []
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        if user_id:
            log.debug("Listing orgs that user_id '%s' is member", user_id)
            orgs = cursor.execute(
                "SELECT o.id, o.name, o.created_at, o.updated_at FROM org_members om INNER JOIN orgs o ON om.user_id = ? AND om.org_id = o.id",
                (user_id,),
            ).fetchall()
        else:
            log.debug("Listing orgs name like '%s'", name_match)
            orgs = cursor.execute(
                "SELECT id, name, created_at, updated_at FROM orgs WHERE name LIKE ?",
                (f"%{name_match}%" if name_match else "%",),
            ).fetchall()

        log.debug("Listing orgs members for orgs: %s", orgs)
        members = cursor.execute(
            "SELECT m.org_id, u.id, u.fullname, m.org_admin FROM org_members m, users u WHERE m.org_id IN ({}) AND m.user_id = u.id".format(  # noqa: S608
                ",".join([str(x[0]) for x in orgs])
            )
        ).fetchall()

        return [(x[0], x[1], [(y[1], y[2], y[3]) for y in members if y[0] == x[0]], x[2], x[3]) for x in orgs]


def _create_organisation_sql(connection_cursor: sqlite3.Cursor, name: str) -> sqlite3.Cursor:
    """Create org.

    Internal function to be called with a connection context. This enables executing the same SQL logic within transaction in multiple places.

    Example:
    ```python
        with closing(
            sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
        ) as connection, closing(connection.cursor()) as cursor:
            try:
                cursor.execute("BEGIN TRANSACTION")
                _create_organisation_cursor(cursor, name, creating_user_id)
                connection.commit()
            except Exception as e:
                # Rollback transaction on error
                connection.rollback()
                log.error("Error creating xxxxxxxxxxxx, rolled back: %s", e)
                raise Exception("Error creating xxxxxxxxxx. DB Transaction rolled back.") from e
    ```
    """
    connection_cursor.execute(
        "INSERT INTO orgs (name) VALUES (?)",
        (name,),
    )

    return connection_cursor


def create_organisation(name: str, creating_user_id: int) -> int | None:
    """Create an org.

    Args:
        name (str): The org name.
        creating_user_id (int): The user id of the user creating the org. This user will be the first org admin.

    Returns:
        int: org id if successful or None otherwise.
    """
    org_id = None
    log.debug("Creating org: %s", name)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        try:
            cursor.execute("BEGIN TRANSACTION")
            _create_organisation_sql(cursor, name)
            org_id = cursor.lastrowid
            is_default_org_admin = True
            manage_users._add_organisation_member_sql(cursor, org_id, creating_user_id, is_default_org_admin)
            connection.commit()
            log.info("Created organization %s with member %s", org_id, creating_user_id)
        except Exception as e:
            # Rollback transaction on error
            connection.rollback()
            log.error("Error creating organization with member, rolled back: %s", e)
            raise Exception("Error creating organization with member. DB Transaction rolled back.", e) from e
    if org_id:
        manage_settings._init_default_org_settings(org_id)
    return org_id


def update_organisation(id_: int, name: str = None) -> bool:
    """Update a group.

    Args:
        id_ (int): The group id.
        name (str, optional): The group name. Defaults to None.

    Returns:
        bool: True if the orgs is updated, False otherwise.
    """
    log.debug("Updating org: %d, name: %s", id_, name)

    query = "UPDATE orgs SET updated_at = ?"
    params = [
        datetime.now(),
    ]

    if name:
        query += ", name = ?"
        params.append(name)

    query += " WHERE id = ?"
    params.append(id_)
    log.debug("Update org query: %s, params: %s", query, params)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        try:
            cursor.execute(query, tuple(params))
            connection.commit()
            return True
        except Exception as e:
            log.error("Error updating org: %s", e)
            return False


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
