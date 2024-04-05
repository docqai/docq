"""Slack messages handler."""

import sqlite3
from contextlib import closing

from ...support.store import get_sqlite_org_slack_messages_file
from .models import SlackMessage

SQL_CREATE_TABLE_DOCQ_SLACK_MESSAGES = """
CREATE TABLE IF NOT EXISTS docq_slack_messages (
    id INTEGER PRIMARY KEY,
    client_msg_id TEXT NOT NULL, -- Unique identifier for the message
    type TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    team_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    text TEXT NOT NULL,
    ts TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def _init(org_id: int) -> None:
    """Initialize the Slack integration."""
    with closing(sqlite3.connect(get_sqlite_org_slack_messages_file(org_id=org_id))) as connection:
        connection.execute(SQL_CREATE_TABLE_DOCQ_SLACK_MESSAGES)
        connection.commit()


def insert_or_update_message(
    client_msg_id: str, type_: str, channel: str, team: str, user: str, text: str, ts: str, org_id: int
) -> None:
    """Insert or update a message."""
    _init(org_id)
    with closing(sqlite3.connect(get_sqlite_org_slack_messages_file(org_id=org_id))) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO docq_slack_messages (client_msg_id, type, channel_id, team_id, user_id, text, ts) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (client_msg_id, type_, channel, team, user, text, ts),
        )
        connection.commit()


def is_message_handled(client_msg_id: str, ts: str, org_id: int) -> bool:
    """Check if a message exists."""
    _init(org_id)
    with closing(sqlite3.connect(get_sqlite_org_slack_messages_file(org_id=org_id))) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM docq_slack_messages WHERE client_msg_id = ? AND ts = ?",
            (client_msg_id, ts),
        )
        return cursor.fetchone() is not None


def list_slack_messages(channel: str, org_id: int) -> list[SlackMessage]:
    """Get a list of messages for a specific channel."""
    _init(org_id)
    with closing(sqlite3.connect(get_sqlite_org_slack_messages_file(org_id=org_id))) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT client_msg_id, type, channel_id, team_id, user_id, text, ts, created_at FROM docq_slack_messages WHERE channel = ?",
            (channel,),
        )
        rows = cursor.fetchall()
        return [
            SlackMessage(
                client_msg_id=row[0],
                type=row[1],
                channel_id=row[2],
                team_id=row[3],
                user_id=row[4],
                text=row[5],
                ts=row[6],
                created_at=row[7],
            )
            for row in rows
        ]
