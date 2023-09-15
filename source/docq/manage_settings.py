"""Functions to manage settings.

Three scopes are supported:

- Org: settings that apply to all users in a specific org. user_id=USER_ID_AS_SYSTEM
- User Org: settings that apply to a specific user scoped to an org.
"""

import json
import logging as log
import sqlite3
from contextlib import closing
from typing import Any

from .config import SystemSettingsKey, UserSettingsKey
from .support.store import get_sqlite_system_file, get_sqlite_usage_file

SQL_CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    user_id INTEGER NOT NULL,
    org_id INTEGER NOT  NULL,
    key TEXT,
    val TEXT,
    PRIMARY KEY (user_id, org_id, key)
)
"""


USER_ID_AS_SYSTEM = 0


def _init(user_id: int = None) -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SETTINGS_TABLE)
        connection.commit()


def _get_sqlite_file(user_id: int = None) -> str:
    """Get the sqlite file for the given user."""
    return get_sqlite_usage_file(user_id) if user_id else get_sqlite_system_file()


def _get_settings(org_id: int, user_id: int = None) -> dict:
    log.debug("Getting settings for user %s", str(user_id))
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        id_ = user_id or USER_ID_AS_SYSTEM
        rows = cursor.execute(
            "SELECT key, val FROM settings WHERE user_id = ? AND org_id = ?",
            (id_, org_id),
        ).fetchall()
        if rows:
            return {key: json.loads(val) for key, val in rows}
        return {}


def _update_settings(settings: dict, org_id: int, user_id: int = None) -> bool:
    log.debug("Updating settings for user %d", user_id)
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        user_id = user_id or USER_ID_AS_SYSTEM
        # _org_id = org_id or ORG_ID_AS_SYSTEM
        cursor.executemany(
            "INSERT OR REPLACE INTO settings (user_id, org_id, key, val) VALUES (?, ?, ?, ?)",
            [(user_id, org_id, key, json.dumps(val)) for key, val in settings.items()],
        )
        connection.commit()
        return True


def get_org_system_settings(org_id: int, key: SystemSettingsKey = None) -> Any | None:
    """Get the system settings. Applies to all users in an org."""
    return _get_settings(org_id=org_id) if key is None else _get_settings(org_id=org_id).get(key.name)


def get_user_settings(org_id: int, user_id: int, key: UserSettingsKey = None) -> Any | None:
    """Get the user settings scoped to an org."""
    return (
        _get_settings(org_id=org_id, user_id=user_id)
        if key is None
        else _get_settings(org_id=org_id, user_id=user_id).get(key.name)
    )


def update_system_settings(settings: dict, org_id: int) -> bool:
    """Update the system settings. Applies to all users in an org."""
    return _update_settings(org_id=org_id, settings=settings)


def update_user_settings(user_id: int, settings: dict, org_id: int) -> bool:
    """Update the user settings."""
    return _update_settings(settings, org_id, user_id)
