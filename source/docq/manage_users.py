"""Functions to manage users."""

import logging as log
import random
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Tuple

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from opentelemetry import trace

import docq

from . import manage_documents as mdocuments
from . import manage_organisations
from . import manage_settings as msettings
from .config import SpaceType
from .domain import SpaceKey
from .support.store import get_sqlite_system_file

trace = trace.get_tracer(__name__, str(docq.__version__))

SQL_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    fullname TEXT,
    super_admin BOOL default 0,
    archived BOOL DEFAULT 0,
    verified BOOL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SQL_CREATE_ORG_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS org_members (
    org_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    org_admin BOOL DEFAULT 0,
    FOREIGN KEY (org_id) REFERENCES orgs (id),
    FOREIGN KEY (user_id) REFERENCES users (id),
    PRIMARY KEY (org_id, user_id)
)
"""

DIGEST_SIZE = 32
DEFAULT_ADMIN_ID = 1000
DEFAULT_ADMIN_USERNAME = "docq"
DEFAULT_ADMIN_PASSWORD = "Docq.AI"
DEFAULT_ADMIN_FULLNAME = "Docq Admin"

PH = PasswordHasher()

@trace.start_as_current_span(name="manage_users._init")
def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_USERS_TABLE)
        cursor.execute(SQL_CREATE_ORG_MEMBERS_TABLE)
        connection.commit()

@trace.start_as_current_span(name="manage_users._init_admin_if_necessary")
def _init_admin_if_necessary() -> bool:
    created = False
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        (count,) = cursor.execute("SELECT COUNT(*) FROM users WHERE super_admin = ?", (1,)).fetchone()
        if int(count) > 0:
            log.debug("%d super_admin user found, skipping...", count)
            return False
        else:
            log.info("No super_admin user found, creating one with default values...")
            password = PH.hash(DEFAULT_ADMIN_PASSWORD)
            cursor.execute(
                "INSERT INTO users (id, username, password, fullname, super_admin, verified) VALUES (?, ?, ?, ?, ?, ?)",
                (DEFAULT_ADMIN_ID, DEFAULT_ADMIN_USERNAME, password, DEFAULT_ADMIN_FULLNAME, 1, 1),
            )
            connection.commit()
            add_organisation_member(manage_organisations.DEFAULT_ORG_ID, DEFAULT_ADMIN_ID, True)
            created = True

    # Reindex the user's space for the first time
    if created:
        _reindex_user_docs(DEFAULT_ADMIN_ID, manage_organisations.DEFAULT_ORG_ID)

    return created

@trace.start_as_current_span(name="manage_users._init_user_data")
def _init_user_data(user_id: int) -> None:
    msettings._init(user_id)
    log.info("Initialised user data for user: %d", user_id)


@trace.start_as_current_span(name="manage_users._reindex_user_docs")
def _reindex_user_docs(user_id: int, org_id: int) -> None:
    mdocuments.reindex(SpaceKey(SpaceType.PERSONAL, user_id, org_id))

@trace.start_as_current_span(name="manage_users.authenticate")
def authenticate(username: str, password: str) -> Tuple[int, str, bool, str]:
    """Authenticate a user.

    Args:
        username (str): The username.
        password (str): The password.

    Returns:
        tuple[int, str, bool, str]: The [user's id, fullname, super_admin status, username] if authenticated, `None` otherwise.
    """
    log.debug("Authenticating user: %s", username)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        selected = cursor.execute(
            "SELECT id, password, fullname, super_admin, verified FROM users WHERE username = ? AND archived = 0",
            (username,),
        ).fetchone()
        if selected:
            log.debug("User found: %s", selected)
            (id_, saved_password, fullname, super_admin, verified) = selected
            if not verified:
                log.warning("User: %s is not verified", username)
                return None
            try:
                result = (id_, fullname, super_admin, username) if PH.verify(saved_password, password) else None
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

@trace.start_as_current_span(name="manage_users.get_user")
def get_user(user_id: int = None, username: str = None) -> Tuple[int, str, str, bool, bool, datetime, datetime] | None:
    """Get a user.

    Args:
        user_id (int): The user id. Default to None. If not `None` takes precedence over username.
        username (str): The username. Default to None.

    Returns:
        If no match is found return `None` else return a tuple with user data as follows:
        tuple[int, str, str, bool, bool, datetime, datetime]: The user [user_id, username, fullname, super_admin, archived, created_at, updated_at].
    """
    log.debug("Getting user: %s, %s", user_id, username)
    query = "SELECT id, username, fullname, super_admin, archived, created_at, updated_at FROM users WHERE"
    params = []

    if user_id:
        query += " id = ?"
        params.append(user_id)
    elif username:
        query += " username = ?"
        params.append(username)
    else:
        raise ValueError("Either user_id or username must be provided")

    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        return cursor.execute(
            query,
            tuple(params),
        ).fetchone()

@trace.start_as_current_span(name="manage_users.list_users")
def list_users(username_match: str = None) -> List[Tuple[int, str, str, bool, bool, datetime, datetime]]:
    """List users.

    Args:
        username_match (str, optional): The username match. Defaults to None.

    Returns:
        List[Tuple[int, str, str, bool, bool, datetime, datetime]]: The list of users [user id, username, fullname, super_admin, archived, created_at, updated_at].
    """
    log.debug("Listing users: %s", username_match)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        return cursor.execute(
            "SELECT id, username, fullname, super_admin, archived, created_at, updated_at FROM users WHERE username LIKE ?",
            (f"%{username_match}%" if username_match else "%",),
        ).fetchall()

@trace.start_as_current_span(name="manage_users.list_users_by_org")
def list_users_by_org(
    org_id: int, username_match: str = None, org_admin_match: bool = None
) -> List[Tuple[int, int, str, str, bool, bool, bool, datetime, datetime]]:
    """List users that are a member of an org.

    Args:
        username_match (str, optional): The username match. Defaults to None.
        org_id (int): The org id.
        org_admin_match (bool, optional): Whether the user is an org admin. Defaults to None.

    Returns:
        List[Tuple[int, int, str, str, str, bool, bool, bool, datetime, datetime]]: The list of users [user_id, org_id, username, fullname, is super_admin, is org_admin, is archived, created, updated].
    """
    log.debug("Listing users for org id: %s that username_match: %s", org_id, username_match)

    query = "SELECT u.id, om.org_id, u.username, u.fullname, u.super_admin, om.org_admin, u.archived, u.created_at, u.updated_at FROM org_members om LEFT JOIN users u ON om.org_id = ? AND om.user_id = u.id WHERE username LIKE ?"
    params = [
        org_id,
        f"%{username_match}%" if username_match else "%",
    ]

    if org_admin_match is not None:
        query += " AND om.org_admin = ?"
        params.append(
            org_admin_match,
        )

    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        return cursor.execute(query, tuple(params)).fetchall()

@trace.start_as_current_span(name="manage_users.list_selected_users")
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
            "SELECT id, username, fullname, super_admin, archived, created_at, updated_at FROM users WHERE id IN ({})".format(  # noqa: S608
                ",".join([str(id_) for id_ in ids_])
            )
        ).fetchall()

@trace.start_as_current_span(name="manage_users.update_user")
def update_user(
    id_: int,
    username: str = None,
    password: str = None,
    fullname: str = None,
    super_admin: bool = False,
    org_admin: bool = False,
    archived: bool = False,
) -> bool:
    """Update a user.

    Args:
        id_ (int): The user id.
        username (str, optional): The username. Defaults to None.
        password (str, optional): The password. Defaults to None.
        fullname (str, optional): The full name. Defaults to None.
        super_admin (bool, optional): Whether the user is an super_admin. Defaults to None.
        org_admin (bool, optional): Whether the user is an org_admin. Defaults to None.
        archived (bool, optional): Whether the user is archived. Defaults to None.

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

    query += ", super_admin = ?"
    params.append(super_admin)

    query += ", archived = ?"
    params.append(archived)

    query += " WHERE id = ?"
    params.append(id_)

    log.debug("Query: %s | Params: %s", query, params)

    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(query, tuple(params))
        connection.commit()
        return True

@trace.start_as_current_span(name="manage_users.create_user")
def create_user(
    username: str,
    password: str,
    fullname: str = None,
    super_admin: bool = False,
    org_admin: bool = False,
    org_id: int = None,
) -> int:
    """Create a user.

    Args:
        username (str): The username.
        password (str): The password.
        fullname (str, optional): The full name. Defaults to ''.
        super_admin (bool, optional): Whether the user is a super admin, all the god powers at a system level. Defaults to False.
        org_admin (bool, optional): Whether the user is an org level admin for the `org_id`. Defaults to False.
        org_id (int, optional): The org id to add the user to. Defaults to None.
        verified (bool, optional): Whether the user is verified. Defaults to False.

    Returns:
        bool: True if the user is created, False otherwise.
    """
    log.debug("Creating user: %s", username)
    hashed_password = PH.hash(password)

    def rnd():
        return random.randint(10000, 99999)

    user_id = None
    personal_org_id = None
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute(
                "INSERT INTO users (username, password, fullname, super_admin) VALUES (?, ?, ?, ?)",
                (
                    username,
                    hashed_password,
                    fullname,
                    super_admin,
                ),
            )
            user_id = cursor.lastrowid

            _fullname = fullname if fullname else username
            first_name = _fullname.split(" ")[0]
            personal_org_name = f"{first_name} Personal Org {rnd()}"  # org names must be unique
            log.debug("Creating personal org: %s", personal_org_name)
            manage_organisations._create_organisation_sql(cursor, personal_org_name)

            personal_org_id = cursor.lastrowid

            _add_organisation_member_sql(cursor, personal_org_id, user_id, True)

            if org_id:
                log.info("Adding user %s to org %s", user_id, org_id)
                _add_organisation_member_sql(cursor, org_id, user_id, org_admin)

            connection.commit()
            log.info("Created user %s", user_id)

        except Exception as e:
            user_id = None
            personal_org_id = None
            connection.rollback()
            log.error("Error creating user: %s", e)
            raise ValueError("Error creating user. DB Transaction rolled back.") from e

        if personal_org_id:
            msettings._init_org_settings(personal_org_id)

    return user_id

@trace.start_as_current_span(name="manage_users.set_user_as_verified")
def set_user_as_verified(id_: int) -> bool:
    """Verify a user."""
    log.debug("Verifying user: %d", id_)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "UPDATE users SET verified = ?, updated_at = ? WHERE id = ?",
            (
                1,
                datetime.now(),
                id_,
            ),
        )
        connection.commit()
        return True

@trace.start_as_current_span(name="manage_users.check_account_activated")
def check_account_activated(username: str) -> bool:
    """Check if a user's account is activated.

    Args:
        username (str): The username (email).

    Returns:
        bool: True if the user's account is activated, False otherwise.
    """
    with closing(sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)) as connection:
        return (
            connection.execute(
                "SELECT id FROM users WHERE username = ? AND verified = ?",
                (username, 1),
            ).fetchone()
            is not None
        )

@trace.start_as_current_span(name="manage_users.reset_password")
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

@trace.start_as_current_span(name="manage_users.archive_user")
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

@trace.start_as_current_span(name="manage_users._add_organisation_member_sql")
def _add_organisation_member_sql(
    connection_cursor: sqlite3.Cursor, org_id: int, user_id: int, org_admin: bool = False
) -> sqlite3.Cursor:
    """Add a user to an org as a member."""
    connection_cursor.execute(
        "INSERT INTO org_members (org_id, user_id, org_admin) VALUES (?, ?, ?)",
        (org_id, user_id, org_admin),
    )
    return connection_cursor

@trace.start_as_current_span(name="manage_users.add_organisation_member")
def add_organisation_member(org_id: int, user_id: int, org_admin: bool = False) -> bool:
    """Add a user to an org as a member.

    Return:
        bool: True if the user is added to the org successfully, False otherwise.
    """
    log.debug("Adding user: %s to org: %s", user_id, org_id)
    success = False
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        try:
            _add_organisation_member_sql(cursor, org_id, user_id, org_admin)
            connection.commit()
            success = True
        except Exception as e:
            success = False
            log.error(
                "add_organisation_member(): Error adding user_id '%s' to org_id '%s'. Error: %s", user_id, org_id, e
            )
    return success

@trace.start_as_current_span(name="manage_users.user_is_org_member")
def user_is_org_member(org_id: int, user_id: int) -> bool:
    """Check if a user is a member of an org.

    Args:
        org_id (int): The org id.
        user_id (int): The user id.

    Returns:
        bool: True if the user is a member of the org, False otherwise.
    """
    log.debug("Checking if user: %s is a member of org: %s", user_id, org_id)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        return (
            cursor.execute(
                "SELECT * FROM org_members WHERE org_id = ? AND user_id = ?",
                (org_id, user_id),
            ).fetchone()
            is not None
        )

@trace.start_as_current_span(name="manage_users.update_organisation_members")
def update_organisation_members(org_id: int, users: List[Tuple[int, bool]]) -> bool:
    """Update org members.

    Args:
        org_id (int): The org id.
        users (List[Tuple[int, bool]]): The list fo users [user id, org_admin].

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
                "INSERT INTO org_members (org_id, user_id, org_admin) VALUES (?, ?, ?)",
                [(org_id, x[0], x[1]) for x in users],
            )
            connection.commit()
            success = True
        except Exception as e:
            success = False
            connection.rollback()
            log.error("Error updating org members, rolled back: %s", e)

    return success
