"""Functions to manage sharing of spaces."""

import logging as log
import sqlite3
from contextlib import closing

from .support.store import get_sqlite_system_file

SQL_CREATE_SHARING_TABLE = """
CREATE TABLE IF NOT EXISTS sharing (
    id INTEGER PRIMARY KEY,
    user_id INTEGER references user(id),
    space_id INTEGER references space(id)
)
"""


def associate_user_with_space(user_id: int, space_id: int, by: int) -> bool:
    """Associate a user with a space.

    Args:
        user_id (int): The user id.
        space_id (int): The space id.
        by (int): The user id of the user who is associating the user with the space.

    Returns:
        bool: True if the user is associated with the space, False otherwise.
    """
    log.debug("Associating user %d with space %d by %d", user_id, space_id, by)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SHARING_TABLE)
        cursor.execute(
            "INSERT INTO access (user_id, space_id) VALUES (?, ?)",
            (
                user_id,
                space_id,
            ),
        )
        connection.commit()
        return True


def dissociate_user_from_space(user_id: int, space_id: int, by: int) -> bool:
    """Dissociate a user from a space.

    Args:
        user_id (int): The user id.
        space_id (int): The space id.
        by (int): The user id of the user who is dissociating the user from the space.

    Returns:
        bool: True if the user is dissociated from the space, False otherwise.
    """
    log.debug("Dissociating user %d from space %d by %s", user_id, space_id, by)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SHARING_TABLE)
        cursor.execute(
            "DELETE FROM sharing WHERE user_id = ? AND space_id = ?",
            (
                user_id,
                space_id,
            ),
        )
        connection.commit()
        return True
