"""Functions to manage settings.

Three scopes are supported:

- Org: settings that apply to all users in a specific org. user_id=USER_ID_AS_SYSTEM
- User Org: settings that apply to a specific user scoped to an org.
"""

import json
import logging as log
import sqlite3
from contextlib import closing
from typing import Any, Optional

from opentelemetry import trace

import docq

from .config import (
    OrganisationFeatureType,
    OrganisationSettingsKey,
    SystemFeatureType,
    SystemSettingsKey,
    UserSettingsKey,
)
from .constants import DEFAULT_ORG_ID
from .support.store import get_sqlite_system_file, get_sqlite_usage_file

tracer = trace.get_tracer(__name__, docq.__version_str__)

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
ORG_ID_AS_SYSTEM = 0




@tracer.start_as_current_span("_init_org_settings")
def _init_default_org_settings(org_id: int) -> None:
    """Initialise org settings with defaults."""
    update_organisation_settings(
        {
            OrganisationSettingsKey.ENABLED_FEATURES.name: [
                OrganisationFeatureType.ASK_PERSONAL.name,
                OrganisationFeatureType.ASK_PUBLIC.name,
                OrganisationFeatureType.ASK_SHARED.name,
                OrganisationFeatureType.CHAT_PRIVATE.name,
            ],
            OrganisationSettingsKey.MODEL_COLLECTION.name: "azure_openai_with_local_embedding",
        },
        org_id=org_id,
    )
    log.debug("Org setting initialised with defaults for org_id: %s", org_id)

@tracer.start_as_current_span("_init_default_system_settings")
def _init_default_system_settings() -> None:
    """Initialise system settings with defaults."""
    update_system_settings(
        {
            SystemSettingsKey.ENABLED_FEATURES.name: [SystemFeatureType.FREE_USER_SIGNUP.name],
        },
    )
    log.debug("System setting initialised with defaults")

@tracer.start_as_current_span("manage_settings._init")
def _init(user_id: Optional[int] = None) -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SETTINGS_TABLE)
        connection.commit()
    _init_default_system_settings()
    _init_default_org_settings(DEFAULT_ORG_ID)

def _get_sqlite_file(user_id: Optional[int] = None) -> str:
    """Get the sqlite file for the given user."""
    return get_sqlite_usage_file(user_id) if user_id else get_sqlite_system_file()


def _get_settings(org_id: int, user_id: int) -> dict[str, str]:
    log.debug("Getting settings for user '%s'", str(user_id))
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        rows = cursor.execute(
            "SELECT key, val FROM settings WHERE user_id = ? AND org_id = ?",
            (user_id, org_id),
        ).fetchall()
        if rows:
            return {key: json.loads(val) for key, val in rows}
        return {}


def _update_settings(settings: dict, org_id: int, user_id: Optional[int] = None) -> bool:
    with closing(
        sqlite3.connect(_get_sqlite_file(user_id), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        user_id = user_id or USER_ID_AS_SYSTEM
        log.debug("Updating settings for user %d", user_id)
        cursor.executemany(
            "INSERT OR REPLACE INTO settings (user_id, org_id, key, val) VALUES (?, ?, ?, ?)",
            [(user_id, org_id, key, json.dumps(val)) for key, val in settings.items()],
        )
        connection.commit()
        return True



def get_system_settings(key: Optional[SystemSettingsKey] = None) -> dict | str | None:
    """Get the system settings. Applies to all users in an org."""
    return (
        _get_settings(org_id=ORG_ID_AS_SYSTEM, user_id=USER_ID_AS_SYSTEM)
        if key is None
        else _get_settings(org_id=ORG_ID_AS_SYSTEM, user_id=USER_ID_AS_SYSTEM).get(key.name)
    )


def get_organisation_settings(org_id: int, key: Optional[OrganisationSettingsKey] = None) -> dict | str | None:
    """Get the system settings. Applies to all users in an org."""
    return (
        _get_settings(org_id=org_id, user_id=USER_ID_AS_SYSTEM)
        if key is None
        else _get_settings(org_id=org_id, user_id=USER_ID_AS_SYSTEM).get(key.name)
    )


def get_user_settings(org_id: int, user_id: int, key: Optional[UserSettingsKey] = None) -> dict | str | None:
    """Get the user settings scoped to an org."""
    return (
        _get_settings(org_id=org_id, user_id=user_id)
        if key is None
        else _get_settings(org_id=org_id, user_id=user_id).get(key.name)
    )


def update_system_settings(settings: dict) -> bool:
    """Update the system settings."""
    return _update_settings(settings=settings, org_id=ORG_ID_AS_SYSTEM, user_id=USER_ID_AS_SYSTEM)

def update_organisation_settings(settings: dict, org_id: int) -> bool:
    """Update the system settings. Applies to all users in an org."""
    return _update_settings(settings=settings, org_id=org_id, user_id=USER_ID_AS_SYSTEM)


def update_user_settings(user_id: int, settings: dict, org_id: int) -> bool:
    """Update the user settings."""
    return _update_settings(settings=settings, org_id=org_id, user_id=user_id)
