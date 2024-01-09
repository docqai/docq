"""Database migration scripts for schema changes etc."""

import logging
import sqlite3
from contextlib import closing

from opentelemetry import trace

import docq
from docq.support.store import SpaceType, get_sqlite_system_file

tracer = trace.get_tracer(__name__, docq.__version_str__)


@tracer.start_as_current_span("docq.db_migrations.run")
def run() -> None:
    """Run database migrations.

    Call this after all tables are created.
    """
    migration_sample1()
    add_space_type_to_spaces()


def migration_sample1() -> None:
    """Sample migration script."""
    with tracer.start_as_current_span("docq.db_migrations.migration_sample") as span:
        try:
            logging.info("Running migration sample")
            span.add_event("Running migration sample")
            # do some migration work
            logging.info("Migration sample complete successfully")
            span.set_attribute("migration_successful", "true")
        except Exception as e:
            logging.error("Migration XYZ sample failed")
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Migration sample failed"))
            span.record_exception(e)
            raise Exception("Migration XYZ failed") from e


def add_space_type_to_spaces() -> None:
    """Add space_type column to spaces table.

    Check if space_type column exists in spaces table. if exists log and return.

    Create space_type column in spaces table with parameter space_type TEXT NOT NULL.
    UPDATE spaces SET space_type = SpaceType.SHARED.name for all existing rows.
    """
    with tracer.start_as_current_span("docq.db_migrations.add_space_type_to_spaces") as span:
        try:
            span.add_event("Running migration add_space_type_to_spaces")
            logging.info("Running migration add_space_type_to_spaces")

            with closing(sqlite3.connect(get_sqlite_system_file())) as connection, closing(connection.cursor()) as cursor:
                cursor.execute("PRAGMA table_info(spaces)")
                rows = cursor.fetchall()

                space_type_column_exists = False
                logging.info("db_migrations.add_space_type_to_spaces, Found columns in spaces table: %s", rows)
                for row in rows:
                    if row[1] == "space_type":
                        logging.info("db_migrations.add_space_type_to_spaces, space_type column exists: %s", row)
                        space_type_column_exists = True
                        break

                if not space_type_column_exists:
                    logging.info("db_migrations.add_space_type_to_spaces, space_type column does not exist, adding it")
                    try:
                        cursor.execute("BEGIN TRANSACTION")
                        cursor.execute("ALTER TABLE spaces ADD COLUMN space_type TEXT NOT NULL")
                        cursor.execute("UPDATE spaces SET space_type = ?", (SpaceType.SHARED.name,))
                        connection.commit()
                        logging.info("db_migrations.add_space_type_to_spaces, space_type column added successfully")
                        span.set_attribute("migration_successful", "true")

                    except sqlite3.Error as e:
                        logging.error("db_migrations.add_space_type_to_spaces, failed to add space_type column to spaces table %s", e)
                        span.set_attribute("migration_successful", "false")
                        connection.rollback()

        except Exception as e:
            logging.error("Migration add_space_type_to_spaces failed")
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Migration add_space_type_to_spaces failed"))
            span.record_exception(e)
            raise Exception("Migration add_space_type_to_spaces failed") from e
