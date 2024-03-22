"""Manage integrations with third-party services."""

import logging
import sqlite3
from contextlib import closing
from typing import Optional

from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.support.store import get_sqlite_external_system_file, get_sqlite_shared_system_file
from slack_sdk.oauth.installation_store import Installation

from .models import SlackChannel, SlackInstallation, SlackMessage

SQL_CREATE_DOCQ_SLACK_APPLICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS docq_slack_installations (
    id INTEGER PRIMARY KEY,
    app_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    team_name TEXT NOT NULL, -- References a slack workspace
    org_id INTEGER NOT NULL,
    space_group_id INTEGER, -- TODO: Implement globally available content for the entire slack workspace
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES orgs(id),
    FOREIGN KEY (space_group_id) REFERENCES space_groups(id),
    UNIQUE (app_id, team_id, org_id)
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
    FOREIGN KEY (space_group_id) REFERENCES space_groups(id),
    UNIQUE (channel_id, org_id)
);
"""

SQL_CREATE_TABLE_DOCQ_SLACK_MESSAGES = """
CREATE TABLE IF NOT EXISTS docq_slack_messages (
    id INTEGER PRIMARY KEY,
    client_msg_id TEXT NOT NULL, -- Unique identifier for the message
    type TEXT NOT NULL,
    channel TEXT NOT NULL,
    team TEXT NOT NULL,
    user TEXT NOT NULL,
    text TEXT NOT NULL,
    ts TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (channel) REFERENCES docq_slack_channels(channel_id),
    FOREIGN KEY (team) REFERENCES docq_slack_installations(team_id)
);
"""

def _init() -> None:
    """Initialize the Slack integration."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(SQL_CREATE_DOCQ_SLACK_APPLICATIONS_TABLE)
        connection.execute(SQL_CREATE_DOCQ_SLACK_CHANNELS_TABLE)
        connection.execute(SQL_CREATE_TABLE_DOCQ_SLACK_MESSAGES)
        connection.commit()


def create_docq_slack_installation(installation: Installation, org_id: int) -> None:
    """Create a Docq installation."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO docq_slack_installations (app_id, team_id, team_name, org_id) VALUES (?, ?, ?, ?)",
            (installation.app_id, installation.team_id, installation.team_name, org_id),
        )
        connection.commit()


def update_docq_slack_installation(app_id: str, team_name: str, org_id: int, space_group_id: int) -> None:
    """Update a Docq installation."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "UPDATE docq_slack_installations SET space_group_id = ? WHERE app_id = ? AND team_name = ? AND org_id = ?",
            (space_group_id, app_id, team_name, org_id),
        )
        connection.commit()


def list_docq_slack_installations(org_id: int) -> list[SlackInstallation]:
    """List Docq installations."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT app_id, team_id, team_name, org_id, space_group_id, created_at FROM docq_slack_installations WHERE org_id = ?",
            (org_id,),
        )
        return [SlackInstallation(row) for row in cursor.fetchall()]


def get_docq_slack_installation(app_id: str, team_id: str, org_id: int) -> SlackInstallation:
    """Get a Docq installation."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT app_id, team_id, team_name, org_id, space_group_id, created_at FROM docq_slack_installations WHERE app_id = ? AND team_id = ? AND org_id = ?",
            (app_id, team_id, org_id),
        )
        return SlackInstallation(cursor.fetchone())


def integration_exists(app_id: str, team_id: str, selected_org_id: int) -> bool:
    """Check if an integration exists."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM docq_slack_installations WHERE app_id = ? AND team_id = ? AND org_id = ?",
            (app_id, team_id, selected_org_id),
        )
        return cursor.fetchone() is not None


def insert_or_update_slack_channel(channel_id: str, channel_name: str, org_id: int) -> None:
    """Insert or update a channel."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO docq_slack_channels (channel_id, channel_name, org_id) VALUES (?, ?, ?)",
            (channel_id, channel_name, org_id),
        )
        connection.commit()


def link_space_group_to_slack_channel(org_id: int, channel_id: str, channel_name: str, space_group_id: int,) -> None:
    """Add a space group to a channel."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO docq_slack_channels (space_group_id, channel_id, channel_name, org_id) VALUES (?, ?, ?, ?)",
            (space_group_id, channel_id, channel_name, org_id),
        )
        connection.commit()


def get_slack_channel_linked_space_group_id(org_id: int, channel_id: str) -> Optional[int]:
    """Get a channel space group id."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT space_group_id FROM docq_slack_channels WHERE channel_id = ? AND org_id = ?",
                (channel_id, org_id),
            )
            result = cursor.fetchone()
            return result[0] if result is not None else None
        except sqlite3.OperationalError:
            logging.error("No installations found.")
            return None


def list_slack_channels(org_id: int) -> list[SlackChannel]:
    """List Slack channels."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT channel_id, channel_name, org_id, space_group_id, created_at FROM docq_slack_channels WHERE org_id = ?",
            (org_id,),
        )
        return [SlackChannel(row) for row in cursor.fetchall()]


def get_slack_channel(channel_id: str) -> SlackChannel:
    """Get a channel."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT channel_id, channel_name, org_id, space_group_id, created_at FROM docq_slack_channels WHERE channel_id = ?",
            (channel_id,),
        )
        return SlackChannel(cursor.fetchone())


def get_slack_bot_token(app_id: str, team_id: str) -> str:
    """Get a bot token."""
    with closing(sqlite3.connect(get_sqlite_external_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT bot_token FROM slack_bots WHERE app_id = ? AND team_id = ?", (app_id, team_id)
        )
        return cursor.fetchone()[0]

def get_rag_spaces(channel_id: str) -> Optional[list[SpaceKey]]:
    """Get a list of spaces configured for the given channel."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT s.id, s.org_id, s.name, s.summary, s.archived, s.datasource_type, s.datasource_configs, s.space_type, s.created_at, s.updated_at
            FROM spaces s
            JOIN space_group_members ON s.id = space_group_members.space_id
            JOIN docq_slack_channels ON space_group_members.group_id = docq_slack_channels.space_group_id
            WHERE docq_slack_channels.channel_id = ?
            """,
            (channel_id,),
        )
        spaces = cursor.fetchall()

        return [ SpaceKey(SpaceType[row[7]], row[0], row[1], row[3]) for row in spaces ] if spaces else None


def get_org_id_from_channel_id(channel_id: str) -> Optional[int]:
    """Get the org id from a channel id."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT org_id FROM docq_slack_channels WHERE channel_id = ?", (channel_id,)
        )
        result = cursor.fetchone()
        return result[0] if result is not None else None


def insert_or_update_message(client_msg_id: str, type_: str, channel: str, team: str, user: str, text: str, ts: str) -> None:
    """Insert or update a message."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO docq_slack_messages (client_msg_id, type, channel, team, user, text, ts) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (client_msg_id, type_, channel, team, user, text, ts),
        )
        connection.commit()


def is_message_handled(client_msg_id: str, ts: str) -> bool:
    """Check if a message exists."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM docq_slack_messages WHERE client_msg_id = ? AND ts = ?",
            (client_msg_id, ts),
        )
        return cursor.fetchone() is not None


def list_slack_messages(channel: str) -> list[SlackMessage]:
    """Get a list of messages for a specific channnel."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT client_msg_id, type, channel, team, user, text, ts, created_at FROM docq_slack_messages WHERE channel = ?",
            (channel,),
        )
        return [SlackMessage(row) for row in cursor.fetchall()]
