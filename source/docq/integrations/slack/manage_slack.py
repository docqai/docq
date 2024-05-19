"""Manage integrations with third-party services."""

import logging
import sqlite3
from contextlib import closing
from typing import Optional

from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.support.store import get_sqlite_shared_system_file
from slack_sdk.oauth.installation_store import Installation

from .models import SlackChannel, SlackInstallation

SQL_CREATE_DOCQ_SLACK_APP_INSTALL_TABLE = """
CREATE TABLE IF NOT EXISTS docq_slack_installations (
    id INTEGER PRIMARY KEY,
    app_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    team_name TEXT NOT NULL, -- References a Slack workspace name
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
    space_group_id INTEGER, -- associates knowledge with the channel
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES orgs(id),
    FOREIGN KEY (space_group_id) REFERENCES space_groups(id),
    UNIQUE (channel_id, org_id)
);
"""

# adding persona per channel.
# move channels table from shared to org scope
# add persona_id column to the table
# handle migration scripts


def _init() -> None:
    """Initialize the Slack integration."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(SQL_CREATE_DOCQ_SLACK_APP_INSTALL_TABLE)
        connection.execute(SQL_CREATE_DOCQ_SLACK_CHANNELS_TABLE)
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


def list_docq_slack_installations(org_id: Optional[int], team_id: Optional[str]) -> list[SlackInstallation]:
    """List Docq installations."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        if org_id:
            criteria = " WHERE org_id = ?"
            params = (org_id,)
        elif team_id:
            criteria = " WHERE team_id = ?"
            params = (team_id,)

        cursor.execute(
            f"SELECT app_id, team_id, team_name, org_id, space_group_id, created_at FROM docq_slack_installations{criteria}",
            params,
        )
        rows = cursor.fetchall()
        return [
            SlackInstallation(
                app_id=row[0], team_id=row[1], team_name=row[2], org_id=row[3], space_group_id=row[4], created_at=row[5]
            )
            for row in rows
        ]


# def get_docq_slack_installation(app_id: str, team_id: str, org_id: int) -> SlackInstallation:
#     """Get a Docq installation."""
#     with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
#         cursor = connection.cursor()
#         cursor.execute(
#             "SELECT app_id, team_id, team_name, org_id, space_group_id, created_at FROM docq_slack_installations WHERE app_id = ? AND team_id = ? AND org_id = ?",
#             (app_id, team_id, org_id),
#         )
#         row = cursor.fetchone()
#         return SlackInstallation(
#             app_id=row[0], team_id=row[1], team_name=row[2], org_id=row[3], space_group_id=row[4], created_at=row[5]
#         )


def integration_exists(app_id: str, team_id: str, selected_org_id: int) -> bool:
    """Check if an integration exists."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM docq_slack_installations WHERE app_id = ? AND team_id = ? AND org_id = ?",
            (app_id, team_id, selected_org_id),
        )
        return cursor.fetchone() is not None


# SLACK CHANNELS


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
        rows = cursor.fetchall()
        return [
            SlackChannel(
                channel_id=row[0], channel_name=row[1], org_id=row[2], space_group_id=row[3], created_at=row[4]
            )
            for row in rows
        ]


def get_slack_channel(channel_id: str) -> SlackChannel:
    """Get a channel."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT channel_id, channel_name, org_id, space_group_id, created_at FROM docq_slack_channels WHERE channel_id = ?",
            (channel_id,),
        )
        row = cursor.fetchone()
        return SlackChannel(
            channel_id=row[0], channel_name=row[1], org_id=row[2], space_group_id=row[3], created_at=row[4]
        )


def get_slack_bot_token(app_id: str, team_id: str) -> str:
    """Get a bot token."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
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
