"""Slack messages handler."""

import sqlite3
from contextlib import closing
from typing import List, Optional

from docq import db_migrations
from llama_index.core.llms import ChatMessage, MessageRole

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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thread_ts TEXT -- ts of the parent message i.e. thread message, if null then unthreaded message
);
"""
#


def _init(org_id: int) -> None:
    """Initialize the Slack integration.

    We don't call this in setup because and org_id context is required.
    """
    with closing(sqlite3.connect(get_sqlite_org_slack_messages_file(org_id=org_id))) as connection:
        connection.execute(SQL_CREATE_TABLE_DOCQ_SLACK_MESSAGES)
        connection.commit()
        db_migrations.add_column_threadts_to_slackmessages_table(org_id)


def insert_or_update_message(
    client_msg_id: str,
    type_: str,
    channel: str,
    team: str,
    user: str,
    text: str,
    ts: str,
    org_id: int,
    thread_ts: Optional[str] = None,
) -> None:
    """Insert or update a message."""
    _init(org_id)
    with closing(sqlite3.connect(get_sqlite_org_slack_messages_file(org_id=org_id))) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO docq_slack_messages (client_msg_id, type, channel_id, team_id, user_id, text, ts, thread_ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (client_msg_id, type_, channel, team, user, text, ts, thread_ts),
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
    """Get a list of messages for a specific channel.

    unthreaded and threaded messages.
    """
    _init(org_id)
    with closing(sqlite3.connect(get_sqlite_org_slack_messages_file(org_id=org_id))) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT client_msg_id, type, channel_id, team_id, user_id, text, ts, thread_ts, created_at FROM docq_slack_messages WHERE channel_id = ?",
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
                thread_ts=row[7],
                created_at=row[8],
            )
            for row in rows
        ]


def list_slack_thread_messages(channel: str, org_id: int, thread_ts: str) -> list[SlackMessage]:
    """Get a list of messages for a specific thread."""
    _init(org_id)
    with closing(sqlite3.connect(get_sqlite_org_slack_messages_file(org_id=org_id))) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT client_msg_id, type, channel_id, team_id, user_id, text, ts, thread_ts, created_at FROM docq_slack_messages WHERE channel_id = ? AND thread_ts = ?",
            (
                channel,
                thread_ts,
            ),
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
                thread_ts=row[7],
                created_at=row[8],
            )
            for row in rows
        ]

def get_slack_thread_messages_as_chat_messages(
    channel: str, org_id: int, thread_ts: str, size: Optional[int] = None
) -> List[ChatMessage]:
    """Retrieve slack thread messages as LlamaIndex ChatMessage objects."""
    result = list_slack_thread_messages(channel, org_id, thread_ts)
    # id, message, human, timestamp, thread_id
    # TODO: if bot user_id then set role assistant
    history_chat_message = [ChatMessage(role=MessageRole.USER, content=x.text) for x in result]

    return history_chat_message
