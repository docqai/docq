"""Database migration scripts for schema changes etc."""

import logging
import sqlite3
from contextlib import closing

from opentelemetry import trace

import docq
from docq.support.store import SpaceType, get_sqlite_system_file

tracer = trace.get_tracer(__name__, docq.__version_str__)


@tracer.start_as_current_span("db_migrations.run")
def run() -> None:
    """Run database migrations.

    Call this after all tables are created.
    """
    migration_sample1()
    add_space_type_to_spaces_table()


def migration_sample1() -> None:
    """Sample migration script."""
    with tracer.start_as_current_span("migration_sample") as span:
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


def add_space_type_to_spaces_table() -> None:
    """Add space_type column to spaces table.

    Check if space_type column exists in spaces table. if exists log and return.

    Create space_type column in spaces table with parameter space_type TEXT NOT NULL.
    UPDATE spaces SET space_type = SpaceType.SHARED.name for all existing rows.
    """
    with tracer.start_as_current_span("add_space_type_to_spaces_table") as span:
        try:
            span.add_event("Running migration add_space_type_to_spaces_table")
            logging.info("Running migration add_space_type_to_spaces_table")

            with closing(sqlite3.connect(get_sqlite_system_file())) as connection, closing(connection.cursor()) as cursor:
                cursor.execute("SELECT name FROM pragma_table_info('spaces') WHERE name = 'space_type'")

                if cursor.fetchone() is None:
                    logging.info("db_migrations.add_space_type_to_spaces_table, space_type column does not exist, adding it")
                    span.add_event("space_type column does not exist, adding it")
                    try:
                        cursor.execute("BEGIN TRANSACTION")
                        cursor.execute("ALTER TABLE spaces ADD COLUMN space_type TEXT NOT NULL DEFAULT '" + SpaceType.SHARED.name + "'",)
                        connection.commit()
                        logging.info("db_migrations.add_space_type_to_spaces_table, space_type column added successfully")
                        span.add_event("space_type column added successfully")
                        span.set_attribute("migration_successful", "true")

                    except sqlite3.Error as e:
                        logging.error("db_migrations.add_space_type_to_spaces_table, failed to add space_type column to spaces table %s", e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, "Migration add_space_type_to_spaces_table failed"))
                        span.set_attribute("migration_successful", "false")
                        span.record_exception(e)
                        connection.rollback()

        except Exception as e:
            logging.error("Migration add_space_type_to_spaces_table failed")
            span.set_status(trace.Status(trace.StatusCode.ERROR, "Migration add_space_type_to_spaces_table failed"))
            span.record_exception(e)
            raise Exception("Migration add_space_type_to_spaces_table failed") from e
