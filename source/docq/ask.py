"""This implements the 'Ask Questions' feature in the app."""
import sqlite3
from contextlib import closing
from datetime import timedelta
import logging as log

from .config import load_index, get_sqlite_file


SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY, message TEXT, human BOOL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)
"""

def _save_message(message, human, space):
    with closing(sqlite3.connect(get_sqlite_file(space), detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_TABLE)
        cursor.execute("INSERT INTO history (message, human) VALUES (?, ?)", (message, human))
        connection.commit()


def question(input, space):
    _save_message(input, True, space)

    index = load_index(space)
    output = index.as_query_engine().query(input)
    log.debug(f"Q: {input}, A: {output}")

    _save_message(output.response if output else None, False, space)

    return output


def history(cutoff, size, space):
    with closing(sqlite3.connect(get_sqlite_file(space), detect_types=sqlite3.PARSE_DECLTYPES)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_TABLE)
        rows = cursor.execute("SELECT * FROM history WHERE timestamp < ? ORDER BY timestamp LIMIT ?", (cutoff, size, )).fetchall()
        log.debug("Documents: %s", rows)
        return rows
