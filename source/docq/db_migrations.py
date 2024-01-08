"""Database migration scripts for schema changes etc."""

import logging

from opentelemetry import trace

import docq

tracer = trace.get_tracer(__name__, docq.__version_str__)


@tracer.start_as_current_span("docq.db_migrations.run")
def run() -> None:
    """Run database migrations.

    Call this after all tables are created.
    """
    migration_sample1()


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
