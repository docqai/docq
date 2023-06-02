"""Functions to manage settings."""

import json
import logging as log
import sqlite3
from contextlib import closing
from enum import Enum

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


class SystemSettingsKey(Enum):
    """System settings keys."""

    ENABLED_FEATURES = "enabled_features"
    MODEL_VENDOR = "model_vendor"


def _get_sqlite_file(user_id: int = None) -> str:
    """Get the sqlite file for the given user."""
    return get_sqlite_usage_file(user_id) if user_id else get_sqlite_system_file()


def _get_settings(user_id: int = None) -> dict:
    log.debug("Getting settings for user %d", user_id)
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SETTINGS_TABLE)
        id_ = user_id or USER_ID_AS_SYSTEM
        rows = cursor.execute(
            "SELECT key, val FROM settings WHERE user_id = ?",
            (id_,),
        ).fetchall()
        if rows:
            return {key: json.loads(val) for key, val in rows}


def _update_settings(settings: dict, user_id: int = None) -> bool:
    log.debug("Updating settings for user %d", user_id)
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SETTINGS_TABLE)
        id_ = user_id or USER_ID_AS_SYSTEM
        cursor.executemany(
            "INSERT OR REPLACE INTO settings (user_id, key, val) VALUES (?, ?, ?)",
            [(id_, key, json.dumps(val)) for key, val in settings.items()],
        )
        connection.commit()
        return True


def get_system_settings() -> dict:
    """Get the system settings."""
    return _get_settings()


def get_user_settings(user_id: int) -> dict:
    """Get the user settings."""
    return _get_settings(user_id)


def update_system_settings(settings: dict) -> bool:
    """Update the system settings."""
    return _update_settings(settings)


def update_user_settings(user_id: int, settings: dict) -> bool:
    """Update the user settings."""
    return _update_settings(settings, user_id)
