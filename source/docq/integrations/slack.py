"""Manage integrations with third-party services."""

import os
import sqlite3
from contextlib import closing
from typing import Union

from docq.support.store import get_sqlite_shared_system_file
from slack_sdk.oauth.installation_store import sqlite3 as sqlite3_installation_store

slack_installation_store = sqlite3_installation_store.SQLite3InstallationStore(
    database=get_sqlite_shared_system_file(),
    client_id=os.environ.get("SLACK_CLIENT_ID", ""),
)


SQL_CREATE_DOCQ_SLACK_APPLICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS docq_slack_installations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id FOREIGN KEY REFERENCES slack_installations(app_id),
    team_name FOREIGN KEY REFERENCES slack_installations(team_name),
    org_id FOREIGN KEY REFERENCES orgs(id),
    space_group_id FOREIGN KEY REFERENCES space_groups(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def _init() -> None:
    """Initialize the Slack integration."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(SQL_CREATE_DOCQ_SLACK_APPLICATIONS_TABLE)
        connection.commit()


def create_docq_slack_installation(app_id: str, team_name: str, org_id: int) -> None:
    """Create a Docq installation."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "INSERT INTO docq_slack_installations (app_id, team_name, org_id) VALUES (?, ?, ?)",
            (app_id, team_name, org_id),
        )
        connection.commit()


def list_docq_installations( org_id: int ) -> list[dict[str, Union[str, int]]]:
    """List Docq installations."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute( "SELECT app_id, team_name, org_id FROM docq_slack_installations WHERE org_id = ?", (org_id,) )
        return cursor.fetchall()


def update_docq_installation( app_id: str, team_name: str, org_id: int, space_group_id: int ) -> None:
    """Update a Docq installation."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        connection.execute(
            "UPDATE docq_slack_installations SET space_group_id = ? WHERE app_id = ? AND team_name = ? AND org_id = ?",
            (space_group_id, app_id, team_name, org_id),
        )
        connection.commit()


def get_docq_installation( app_id: str, team_name: str, org_id: int ) -> dict[str, Union[str, int]]:
    """Get a Docq installation."""
    with closing(sqlite3.connect(get_sqlite_shared_system_file())) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT app_id, team_name, org_id, space_group_id FROM docq_slack_installations WHERE app_id = ? AND team_name = ? AND org_id = ?",
            (app_id, team_name, org_id),
        )
        return cursor.fetchone()
