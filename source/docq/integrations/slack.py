"""Manage integrations with third-party services."""

import logging
import sqlite3
from contextlib import closing
from typing import Optional

from docq.support.store import get_sqlite_shared_system_file
from slack_sdk.oauth.installation_store import Installation

from .models import SlackChannel, SlackInstallation

SQL_CREATE_DOCQ_SLACK_APPLICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS docq_slack_installations (
    id INTEGER PRIMARY KEY,
    app_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    group_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES orgs(id),
    FOREIGN KEY (group_id) REFERENCES space_groups(id)
);
"""

SQL_CREATE_DOCQ_SLACK_CHANNELS_TABLE = """
CREATE TABLE IF NOT EXISTS docq_slack_channels (
    id INTEGER PRIMARY KEY,
    channel_id TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    space_group_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES orgs(id),
    FOREIGN KEY (space_group_id) REFERENCES space_groups(id)
);
"""

def _init() -> None:
    """Initialize the Slack integration."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(SQL_CREATE_DOCQ_SLACK_APPLICATIONS_TABLE)
        connection.execute(SQL_CREATE_DOCQ_SLACK_CHANNELS_TABLE)
        connection.commit()


def create_docq_slack_installation(installation: Installation, org_id: int) -> None:
    """Create a Docq installation."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "INSERT INTO docq_slack_installations (app_id, team_name, org_id) VALUES (?, ?, ?)",
            (installation.app_id, installation.team_name, org_id),
        )
        connection.commit()


def update_docq_slack_installation( app_id: str, team_name: str, org_id: int, space_group_id: int ) -> None:
    """Update a Docq installation."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "UPDATE docq_slack_installations SET space_group_id = ? WHERE app_id = ? AND team_name = ? AND org_id = ?",
            (space_group_id, app_id, team_name, org_id),
        )
        connection.commit()


def list_docq_slack_installations(org_id: int) -> list[ SlackInstallation ]:
    """List Docq installations."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT app_id, team_id, org_id FROM docq_slack_installations WHERE org_id = ?", (org_id,))
        return [ SlackInstallation(row) for row in cursor.fetchall() ]


def get_docq_slack_installation( app_id: str, team_name: str, org_id: int ) -> SlackInstallation:
    """Get a Docq installation."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT app_id, team_name, org_id, space_group_id FROM docq_slack_installations WHERE app_id = ? AND team_name = ? AND org_id = ?",
            (app_id, team_name, org_id),
        )
        return SlackInstallation(cursor.fetchone())


def is_slack_admin_user( user: str ) -> bool:
    """Check if a user is an admin."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT team_id FROM slack_installations WHERE user_id = ?",
                (user,),
            )
            return cursor.fetchone()[0] is not None
        except sqlite3.OperationalError:
            logging.error("No installations found.")
            return False


def add_slack_integration( app_id: str, team_id: str, selected_org_id: int ) -> None:
    """Add a Slack integration."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "INSERT INTO docq_slack_installations (app_id, team_id, org_id) VALUES (?, ?, ?)",
            (app_id, team_id, selected_org_id),
        )
        connection.commit()


def app_exists( app_id: str ) -> bool:
    """Check if an app exists."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT id FROM slack_installations WHERE app_id = ?",
                (app_id,),
            )
            return cursor.fetchone() is not None
        except sqlite3.OperationalError:
            logging.error("No installations found.")
            return False


def get_team_name( team_id: str ) -> Optional[str]:
    """Get a team name."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT team_name FROM slack_installations WHERE team_id = ?",
                (team_id,),
            )
            return cursor.fetchone()[0]
        except sqlite3.OperationalError:
            logging.error("No installations found.")


def team_exists( team_id: str ) -> bool:
    """Check if a team exists."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT id FROM slack_installations WHERE team_id = ?",
                (team_id,),
            )
            return cursor.fetchone() is not None
        except sqlite3.OperationalError:
            logging.error("No installations found.")
            return False


def integration_exists( app_id: str, team_id: str, selected_org_id: int ) -> bool:
    """Check if an integration exists."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM docq_slack_installations WHERE app_id = ? AND team_id = ? AND org_id = ?",
            (app_id, team_id, selected_org_id),
        )
        return cursor.fetchone() is not None


def insert_or_update_slack_channel( channel_id: str, channel_name: str, org_id: int ) -> None:
    """Insert or update a channel."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO docq_slack_channels (channel_id, channel_name, org_id) VALUES (?, ?, ?)",
            (channel_id, channel_name, org_id),
        )
        connection.commit()


def link_space_group_to_slack_channel( channel_id: str, space_group_id: int ) -> None:
    """Add a space group to a channel."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "UPDATE docq_slack_channels SET space_group_id = ? WHERE channel_id = ?",
            (space_group_id, channel_id),
        )
        connection.commit()


def get_slack_channel_linked_space_group_id( channel_id: str ) -> int:
    """Get a channel space group id."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT space_group_id FROM docq_slack_channels WHERE channel_id = ?",
            (channel_id,),
        )
        return cursor.fetchone()[0]


def list_slack_channels( org_id: int ) -> list[ SlackChannel ]:
    """List Slack channels."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT channel_id, channel_name, org_id, space_group_id FROM docq_slack_channels WHERE org_id = ?", (org_id,))
        return [ SlackChannel(row) for row in cursor.fetchall() ]


def get_slack_channel( channel_id: str ) -> SlackChannel:
    """Get a channel."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT channel_id, channel_name, org_id, space_group_id FROM docq_slack_channels WHERE channel_id = ?",
            (channel_id,),
        )
        return SlackChannel(cursor.fetchone())
