"""Functions to manage users."""

import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Tuple

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from . import manage_documents as mdocuments
from . import manage_settings as msettings
from .config import SpaceType
from .domain import SpaceKey
from .support.auth_utils import cache_auth
from .manage_documents import reindex
from .support.auth_utils import cache_auth
from .support.store import get_sqlite_system_file

SQL_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    fullname TEXT,
    admin BOOL default 0,
    archived BOOL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

DIGEST_SIZE = 32
DEFAULT_ADMIN_ID = 1000
DEFAULT_ADMIN_USERNAME = "docq"
DEFAULT_ADMIN_PASSWORD = "Docq.AI"
DEFAULT_ADMIN_FULLNAME = "Docq Admin"

PH = PasswordHasher()


def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_USERS_TABLE)
        connection.commit()


def _init_admin_if_necessary() -> bool:
    created = False
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        (count,) = cursor.execute("SELECT COUNT(*) FROM users WHERE admin = ?", (True,)).fetchone()
        if int(count) > 0:
            log.debug("%d admin user found, skipping...", count)
            return False
        else:
            log.info("No admin user found, creating one with default values...")
            password = PH.hash(DEFAULT_ADMIN_PASSWORD)
            cursor.execute(
                "INSERT INTO users (id, username, password, fullname, admin) VALUES (?, ?, ?, ?, ?)",
                (DEFAULT_ADMIN_ID, DEFAULT_ADMIN_USERNAME, password, DEFAULT_ADMIN_FULLNAME, True),
            )
            connection.commit()
            created = True

    # Reindex the user's space for the first time
    if created:
        _reindex_user_docs(DEFAULT_ADMIN_ID)

    return created


def _init_user_data(user_id: int) -> None:
    msettings._init(user_id)
    log.info("Initialised user data for user: %d", user_id)


def _reindex_user_docs(user_id: int) -> None:
    mdocuments.reindex(SpaceKey(SpaceType.PERSONAL, user_id))

@cache_auth
def authenticate(username: str, password: str) -> Tuple[int, str, bool]:
    """Authenticate a user.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        tuple[id, str, bool]: The user's id, fullname and admin status if authenticated, None otherwise.
    """
    log.debug("Authenticating user: %s", username)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        selected = cursor.execute(
            "SELECT id, password, fullname, admin FROM users WHERE username = ? AND archived = 0",
            (username,),
        ).fetchone()
        if selected:
            log.debug("User found: %s", selected)
            (id_, saved_password, fullname, is_admin) = selected
            try:
                result = (id_, fullname, is_admin, username) if PH.verify(saved_password, password) else None
            except VerificationError as e:
                log.warning("Failing to authenticate user: %s for [%s]", username, e)
                return None

            if PH.check_needs_rehash(saved_password):
                log.info("Rehashing password for user: %s", username)
                cursor.execute(
                    "UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
                    (PH.hash(password), datetime.now(), id_),
                )
                connection.commit()

            if result:
                _init_user_data(id_)
            return result
        else:
            return None


def list_users(username_match: str = None) -> List[Tuple[int, str, str, bool, bool, datetime, datetime]]:
    """List users.

    Args:
        username_match (str, optional): The username match. Defaults to None.

    Returns:
        List[Tuple[int, str, str, str, bool, bool, datetime, datetime]]: The list of users.
    """
    log.debug("Listing users: %s", username_match)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        return cursor.execute(
            "SELECT id, username, fullname, admin, archived, created_at, updated_at FROM users WHERE username LIKE ?",
            (f"%{username_match}%" if username_match else "%",),
        ).fetchall()


def list_selected_users(ids_: List[int]) -> List[Tuple[int, str, str, bool, bool, datetime, datetime]]:
    """List selected users by their ids.

    Args:
        ids_ (List[int]): The list of user ids.

    Returns:
        List[Tuple[int, str, str, str, bool, bool, datetime, datetime]]: The list of users.
    """
    log.debug("Listing users: %s", ids_)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        return cursor.execute(
            "SELECT id, username, fullname, admin, archived, created_at, updated_at FROM users WHERE id IN ({})".format(  # noqa: S608
                ",".join([str(id_) for id_ in ids_])
            )
        ).fetchall()


def update_user(
    id_: int,
    username: str = None,
    password: str = None,
    fullname: str = None,
    is_admin: bool = False,
    is_archived: bool = False,
) -> bool:
    """Update a user.

    Args:
        id_ (int): The user id.
        username (str, optional): The username. Defaults to None.
        password (str, optional): The password. Defaults to None.
        fullname (str, optional): The full name. Defaults to None.
        is_admin (bool, optional): Whether the user is an admin. Defaults to None.
        is_archived (bool, optional): Whether the user is archived. Defaults to None.

    Returns:
        bool: True if the user is updated, False otherwise.
    """
    log.debug("Updating user: %d", id_)

    query = "UPDATE users SET updated_at = ?"
    params = [
        datetime.now(),
    ]

    if username:
        query += ", username = ?"
        params.append(username)
    if password:
        hashed_password = PH.hash(password)
        query += ", password = ?"
        params.append(hashed_password)
    if fullname:
        query += ", fullname = ?"
        params.append(fullname)

    query += ", admin = ?"
    params.append(is_admin)

    query += ", archived = ?"
    params.append(is_archived)

    query += " WHERE id = ?"
    params.append(id_)

    log.debug("Query: %s | Params: %s", query, params)

    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(query, tuple(params))
        connection.commit()
        return True


def create_user(username: str, password: str, fullname: str = None, is_admin: bool = False) -> int:
    """Create a user.

    Args:
        username (str): The username.
        password (str): The password.
        fullname (str, optional): The full name. Defaults to ''.
        is_admin (bool, optional): Whether the user is an admin. Defaults to False.

    Returns:
        bool: True if the user is created, False otherwise.
    """
    log.debug("Creating user: %s", username)
    hashed_password = PH.hash(password)

    rowid = None
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO users (username, password, fullname, admin) VALUES (?, ?, ?, ?)",
            (
                username,
                hashed_password,
                fullname,
                is_admin,
            ),
        )
        rowid = cursor.lastrowid
        connection.commit()

    # Reindex the user's space for the first time
    if rowid:
        _reindex_user_docs(rowid)

    return rowid


def reset_password(id_: int, password: str) -> bool:
    """Reset a user's password.

    Args:
        id_ (int): The user id.
        password (str): The password.

    Returns:
        bool: True if the user's password is reset, False otherwise.
    """
    log.debug("Resetting password for user: %d", id)
    hashed_password = PH.hash(password)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "UPDATE users SET password = ?, updated_at = ? WHERE id = ?",
            (
                hashed_password,
                datetime.now(),
                id_,
            ),
        )
        connection.commit()
        return True


def archive_user(id_: int) -> bool:
    """Archive a user.

    Args:
        id_ (int): The user id.

    Returns:
        bool: True if the user is archived, False otherwise.
    """
    log.debug("Archiving user: %d", id_)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "UPDATE users SET archived = 1, updated_at = ? WHERE id = ?",
            (
                datetime.now(),
                id_,
            ),
        )
        connection.commit()
        return True
