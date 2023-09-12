"""Functions to manage settings."""

import json
import logging as log
import sqlite3
from contextlib import closing
from typing import Any

from .config import FeatureType, SystemSettingsKey, UserSettingsKey
from .domain import FeatureKey
from .support.store import get_sqlite_system_file, get_sqlite_usage_file

SQL_CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    user_id INTEGER,
    key TEXT,
    val TEXT,
    PRIMARY KEY (user_id, key)
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
    return get_sqlite_usage_file(FeatureKey(FeatureType.ASK_PERSONAL, user_id)) if user_id else get_sqlite_system_file()


def _get_settings(user_id: int = None) -> dict:
    log.debug("Getting settings for user %s", str(user_id))
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        id_ = user_id or USER_ID_AS_SYSTEM
        rows = cursor.execute(
            "SELECT key, val FROM settings WHERE user_id = ?",
            (id_,),
        ).fetchall()
        if rows:
            return {key: json.loads(val) for key, val in rows}
        return {}


def _update_settings(settings: dict, user_id: int = None) -> bool:
    log.debug("Updating settings for user %d", user_id)
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        id_ = user_id or USER_ID_AS_SYSTEM
        cursor.executemany(
            "INSERT OR REPLACE INTO settings (user_id, key, val) VALUES (?, ?, ?)",
            [(id_, key, json.dumps(val)) for key, val in settings.items()],
        )
        connection.commit()
        return True


def get_system_settings(key: SystemSettingsKey = None) -> Any | None:
    """Get the system settings."""
    return _get_settings() if key is None else _get_settings().get(key.name)


def get_user_settings(user_id: int, key: UserSettingsKey = None) -> Any | None:
    """Get the user settings."""
    return _get_settings(user_id) if key is None else _get_settings(user_id).get(key.name)


def update_system_settings(settings: dict) -> bool:
    """Update the system settings."""
    return _update_settings(settings)


def update_user_settings(user_id: int, settings: dict) -> bool:
    """Update the user settings."""
    return _update_settings(settings, user_id)
