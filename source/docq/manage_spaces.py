"""Functions to manage spaces."""

import json
import logging as log
import random
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any, List, Optional

from llama_index.core.indices import DocumentSummaryIndex, VectorStoreIndex
from llama_index.core.indices.base import BaseIndex
from llama_index.core.schema import Document
from opentelemetry import trace
from sympy import true

import docq

from .access_control.main import SpaceAccessor, SpaceAccessType
from .config import SpaceType
from .data_source.list import SpaceDataSources
from .domain import DocumentListItem, SpaceKey
from .model_selection.main import LlmUsageSettingsCollection, ModelCapability, get_saved_model_settings_collection
from .support.llm import _get_default_storage_context, _get_service_context
from .support.store import get_index_dir, get_sqlite_shared_system_file

trace = trace.get_tracer(__name__, docq.__version_str__)

SQL_CREATE_SPACES_TABLE = """
CREATE TABLE IF NOT EXISTS spaces (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL,
    name TEXT UNIQUE,
    space_type TEXT NOT NULL,
    summary TEXT,
    archived BOOL DEFAULT 0,
    datasource_type TEXT,
    datasource_configs TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (org_id) REFERENCES orgs (id)
)
"""

SQL_CREATE_SPACE_ACCESS_TABLE = """
CREATE TABLE IF NOT EXISTS space_access (
    space_id INTEGER NOT NULL,
    access_type TEXT NOT NULL,
    accessor_id INTEGER,
    FOREIGN KEY (space_id) REFERENCES spaces (id),
    UNIQUE (space_id, access_type, accessor_id)
)
"""

THREAD_SPACE_NAME_TEMPLATE = "Thread-{thread_id} {summary}"

SPACE = tuple[int, int, str, str, bool, str, dict, str, datetime, datetime]


@trace.start_as_current_span("manage_spaces._init")
def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SPACES_TABLE)
        cursor.execute(SQL_CREATE_SPACE_ACCESS_TABLE)
        connection.commit()


@trace.start_as_current_span("manage_spaces._create_index")
def _create_vector_index(
    documents: List[Document], model_settings_collection: LlmUsageSettingsCollection
) -> VectorStoreIndex:
    # Use default storage and service context to initialise index purely for persisting
    return VectorStoreIndex.from_documents(
        documents,
        storage_context=_get_default_storage_context(),
        service_context=_get_service_context(model_settings_collection),
        kwargs=model_settings_collection.model_usage_settings[ModelCapability.TEXT].additional_args
    )


@trace.start_as_current_span("manage_spaces._create_document_summary_index")
def _create_document_summary_index(
    documents: List[Document], model_settings_collection: LlmUsageSettingsCollection
) -> DocumentSummaryIndex:
    """Create a an index of summaries for each document. This doen't create embedding for each node."""
    return DocumentSummaryIndex(embed_summaries=True).from_documents(
        documents,
        storage_context=_get_default_storage_context(),
        service_context=_get_service_context(model_settings_collection),
        kwargs=model_settings_collection.model_usage_settings[ModelCapability.CHAT].additional_args,
    )


@trace.start_as_current_span("manage_spaces._persist_index")
def _persist_index(index: BaseIndex, space: SpaceKey) -> None:
    """Persist an Space datasource index to disk."""
    index.storage_context.persist(persist_dir=get_index_dir(space))


def _format_space(row: Any) -> SPACE:
    """Format space return value from sql data row.

    Args:
        row: (id, org_id, name, summary, archived, datasource_type, datasource_configs, space_type, created_at, updated_at)

    Returns:
        tuple[int, int, str, str, bool, str, dict, datetime, datetime] - [id, org_id, name, summary, archived, datasource_type, datasource_configs, created_at, updated_at]
    """
    return (row[0], row[1], row[2], row[3], bool(row[4]), row[5], json.loads(row[6]), row[7], row[8], row[9])


@trace.start_as_current_span("manage_spaces.create_space")
def create_space(
    org_id: int, name: str, summary: str, datasource_type: str, datasource_configs: dict, space_type: SpaceType
) -> SpaceKey:
    """Create a space.

    Args:
        org_id: int - The organisation id.
        name: str - Name of the space.
        summary: str - Summary of the space (what the space is all about).
        datasource_type: str - Space datasource type.
        datasource_configs: dict - Space datasource configs.
        space_type: str - Space type (from keys of SpaceType).

    Returns:
        SpaceKey of the created space on success.
    """
    if space_type.name not in SpaceType.__members__:
        raise ValueError(f"Invalid space type {space_type}")

    params = (
        org_id,
        name,
        space_type.name,
        summary,
        datasource_type,
        json.dumps(datasource_configs),
    )
    log.debug("Creating space with params: %s", params)
    rowid = None
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO spaces (org_id, name, space_type, summary, datasource_type, datasource_configs) VALUES (?, ?, ?, ?, ?, ?)",
            params,
        )
        rowid = cursor.lastrowid
        connection.commit()
        if rowid is None:
            raise ValueError("Failed to create space")
        log.debug("Created space with rowid: %d", rowid)
        space = SpaceKey(space_type, rowid, org_id)

    reindex(space)

    return space


@trace.start_as_current_span("manage_spaces.list_space")
def list_space(org_id: int, space_type: Optional[str] = None) -> list[SPACE]:
    """List all spaces of a given type."""
    if (space_type is not None) and (space_type not in SpaceType.__members__):
        raise ValueError(f"Invalid space type {space_type}")

    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        _query = "SELECT id, org_id, name, summary, archived, datasource_type, datasource_configs, space_type, created_at, updated_at FROM spaces WHERE org_id = ?"
        params = (org_id,)

        if space_type is not None:
            _query += " AND space_type = ?"
            params += (space_type,)

        _query += " ORDER BY name"

        cursor.execute(
            _query,
            params,
        )

        rows = cursor.fetchall()
        return [_format_space(row) for row in rows]


@trace.start_as_current_span("manage_spaces.reindex")
def reindex(space: SpaceKey) -> None:
    """Reindex documents in a space from scratch. If an index already exists, it will be overwritten."""
    try:
        log.debug("reindex(): Start...")
        log.debug("reindex(): get saved model settings")
        saved_model_settings = get_saved_model_settings_collection(space.org_id)
        _space_data_source = get_space_data_source(space)
        if _space_data_source is None:
            raise ValueError(f"No data source found for space {space}")
        (ds_type, ds_configs) = _space_data_source
        log.debug("reindex(): get datasource instance")
        documents = SpaceDataSources[ds_type].value.load(space, ds_configs)

        if documents:
            log.debug("reindex(): docs to index, %s", len(documents))
            log.debug("reindex(): first doc metadata: %s", documents[0].metadata)
            log.debug("reindex(): first doc text: %s", documents[0].text)

            summary_index = _create_document_summary_index(documents, saved_model_settings)
            _persist_index(summary_index, space)
    except Exception as e:
        if e.__str__().__contains__("No files found"):
            log.info("Reindex skipped. No documents found in space '%s'", space)
        else:
            log.exception("Error indexing space '%s'. Error: %s", space, e)
    finally:
        log.debug("reindex(): Complete")


@trace.start_as_current_span("manage_spaces.list_documents")
def list_documents(space: SpaceKey) -> List[DocumentListItem]:
    """Return a list of tuples containing the filename, creation time, and size of each file in the space."""
    _space_data_source = get_space_data_source(space)

    if _space_data_source is None:
        raise ValueError(f"No data source found for space {space}")

    (ds_type, ds_configs) = _space_data_source

    space_data_source = SpaceDataSources[ds_type].value

    try:
        documents_list = space_data_source.get_document_list(space, ds_configs)

    except Exception as e:
        log.error(
            "Error listing documents for space '%s' of data source type '%s': %s",
            space,
            space_data_source.get_name(),
            e,
        )
        documents_list = []

    return documents_list


@trace.start_as_current_span("manage_spaces.get_document")
def get_space_data_source(space: SpaceKey) -> tuple[str, dict] | None:
    """Returns the data source type and configuration for the given space.

    Args:
        space (SpaceKey): The space to get the data source for.

    Returns:
        tuple[str, dict]: A tuple containing the data source type and configuration.
    """
    shared_space = get_shared_space(space.id_, space.org_id)
    if shared_space is None:
        raise ValueError(f"No shared space found with id {space.id_} and org_id {space.org_id}")
    (_, _, _, _, _, ds_type, ds_configs, _, _, _) = shared_space

    return ds_type, ds_configs


@trace.start_as_current_span("manage_spaces.get_shared_space")
def get_shared_space(id_: int, org_id: int) -> Optional[SPACE]:
    """Get a shared space."""
    log.debug("get_shared_space(): Getting space with id=%d", id_)
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT id, org_id, name, summary, archived, datasource_type, datasource_configs, space_type, created_at, updated_at FROM spaces WHERE id = ? AND org_id = ?",
            (id_, org_id),
        )
        row = cursor.fetchone()
        return _format_space(row) if row else None


@trace.start_as_current_span("manage_spaces.get_shared_spaces")
def get_shared_spaces(space_ids: List[int]) -> list[SPACE]:
    """Get a shared spaces by ids.

    Returns:
        list[tuple[int, int, str, str, bool, str, dict, datetime, datetime]] - [id, org_id, name, summary, archived, datasource_type, datasource_configs, created_at, updated_at]
    """
    log.debug("get_shared_spaces(): Getting space with ids=%s", space_ids)
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        placeholders = ", ".join("?" * len(space_ids))
        query = "SELECT id, org_id, name, summary, archived, datasource_type, datasource_configs, space_type, created_at, updated_at FROM spaces WHERE id IN ({})".format(  # noqa: S608
            placeholders
        )
        cursor.execute(query, space_ids)
        rows = cursor.fetchall()
        return [_format_space(row) for row in rows]


@trace.start_as_current_span("manage_spaces.update_shared_space")
def update_shared_space(
    id_: int,
    org_id: int,
    name: Optional[str] = None,
    summary: Optional[str] = None,
    archived: bool = False,
    datasource_type: Optional[str] = None,
    datasource_configs: Optional[dict] = None,
) -> bool:
    """Update a shared space."""
    query = "UPDATE spaces SET updated_at = ?"
    params = (datetime.now(),)

    if name:
        query += ", name = ?"
        params += (name,)
    if summary:
        query += ", summary = ?"
        params += (summary,)
    if datasource_type:
        query += ", datasource_type = ?"
        params += (datasource_type,)
    if datasource_configs:
        query += ", datasource_configs = ?"
        params += (json.dumps(datasource_configs),)

    query += ", archived = ?"
    params += (archived,)

    query += " WHERE id = ? AND org_id = ?"
    params += (id_, org_id)

    log.debug("Updating space %d with query: %s | Params: %s", id_, query, params)

    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(query, params)
        connection.commit()
        log.debug("Updated space %d", id_)
        return True


@trace.start_as_current_span("manage_spaces.create_shared_space")
def create_shared_space(
    org_id: int, name: str, summary: str, datasource_type: str, datasource_configs: dict
) -> SpaceKey:
    """Create a shared space."""
    return create_space(
        org_id=org_id,
        name=name,
        summary=summary,
        datasource_type=datasource_type,
        datasource_configs=datasource_configs,
        space_type=SpaceType.SHARED,
    )


@trace.start_as_current_span("manage_spaces.create_thread_space")
def create_thread_space(org_id: int, thread_id: int, summary: str, datasource_type: str) -> SpaceKey:
    """Create a spcace for chat thread uploads."""
    rnd = str(random.randint(56450, 9999999999))
    name = f"Thread-{thread_id} {summary} {rnd}"
    print(f"Creating thread space with name: '{name}'")
    return create_space(
        org_id=org_id,
        name=name,
        summary=summary,
        datasource_type=datasource_type,
        datasource_configs={"name": name, "summary": summary, "thread_id": thread_id},
        space_type=SpaceType.THREAD,
    )


def get_thread_space(org_id: int, thread_id: int) -> SpaceKey | None:
    """Get a space for chat thread uploads.

    NOTE: if this doesn't return it doesn't mean the space doesn't exist as it's filtered by org_id. Use space_name_exists() to check if a space with name already exists.
    """
    result = None
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:

        name = f"Thread-{thread_id} %"
        cursor.execute(
            "SELECT id FROM spaces WHERE org_id = ? AND name LIKE ? AND space_type = ?",
            (org_id, name, SpaceType.THREAD.name),
        )
        row = cursor.fetchone()
        if row:
            result = SpaceKey(SpaceType.THREAD, row[0], org_id)
            log.debug("Found space with Id: %d", row[0])
    return result


def thread_space_exists(thread_id: int) -> bool:
    """Check if a thread space exists. Space names are unique. Thread spaces have a special naming convention based on thread_id. Use this to check if a Space with the generated name already exists."""
    exists = True  # default to true as the safer option
    name = f"Thread-{thread_id} %"
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT id, name FROM spaces WHERE name LIKE ?", (name,))
        row = cursor.fetchone()
        exists = row is not None

    print(f"Thread space exists: {exists}")
    return exists


def list_shared_spaces(org_id: int, user_id: Optional[int] = None) -> list[SPACE]:
    """List all shared spaces."""
    return list_space(org_id, SpaceType.SHARED.name)


def list_thread_spaces(org_id: int) -> list[SPACE]:
    """List all thread spaces."""
    return list_space(org_id, SpaceType.THREAD.name)


@trace.start_as_current_span("manage_spaces.list_public_spaces")
def list_public_spaces(selected_org_id: int, space_group_id: int) -> list[SPACE]:
    """List all public spaces from a given space group."""
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            """
            SELECT s.id, s.org_id, s.name, s.summary, s.archived, s.datasource_type, s.datasource_configs, s.space_type, s.created_at, s.updated_at
            FROM spaces s
            JOIN space_group_members c
            LEFT JOIN space_access sa ON s.id = sa.space_id
            WHERE s.org_id = ? AND c.group_id = ? AND c.space_id = s.id
            AND sa.access_type = ?
            ORDER BY name
            """,
            (selected_org_id, space_group_id, SpaceAccessType.PUBLIC.name),
        )
        rows = cursor.fetchall()
        return [_format_space(row) for row in rows]


@trace.start_as_current_span("manage_spaces.get_shared_space_permissions")
def get_shared_space_permissions(id_: int, org_id: int) -> List[SpaceAccessor]:
    """Get the permissions for a shared space."""
    log.debug("get_shared_space_permissions(): Getting permissions for space with id=%d", id_)
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT sa.access_type, u.id as user_id, u.username as user_name, g.id as group_id, g.name as group_name FROM spaces s LEFT JOIN space_access sa ON s.id = sa.space_id AND sa.space_id = ? AND s.org_id = ? LEFT JOIN users u ON sa.accessor_id = u.id LEFT JOIN user_groups g on sa.accessor_id = g.id",
            (
                id_,
                org_id,
            ),
        )
        rows = cursor.fetchall()
        results = []
        for row in rows:
            if row[0] == SpaceAccessType.PUBLIC.name:
                results.append(SpaceAccessor(SpaceAccessType.PUBLIC))
            elif row[0] == SpaceAccessType.USER.name:
                results.append(SpaceAccessor(SpaceAccessType.USER, row[1], row[2]))
            elif row[0] == SpaceAccessType.GROUP.name:
                results.append(SpaceAccessor(SpaceAccessType.GROUP, row[3], row[4]))
        return results


@trace.start_as_current_span("manage_spaces.update_shared_space_permissions")
def update_shared_space_permissions(id_: int, accessors: List[SpaceAccessor]) -> bool:
    """Update the permissions for a shared space."""
    log.debug("update_shared_space_permissions(): Updating permissions for space with id=%d", id_)
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("DELETE FROM space_access WHERE space_id = ?", (id_,))
        for accessor in accessors:
            if accessor.type_ == SpaceAccessType.PUBLIC:
                cursor.execute(
                    "INSERT INTO space_access (space_id, access_type) VALUES (?, ?)", (id_, SpaceAccessType.PUBLIC.name)
                )
            else:
                cursor.execute(
                    "INSERT INTO space_access (space_id, access_type, accessor_id) VALUES (?, ?, ?)",
                    (id_, accessor.type_.name, accessor.accessor_id),
                )
        connection.commit()
        return True


def get_space(space_id: int, org_id: int) -> Optional[SPACE]:
    """Get a space."""
    log.debug("get_space(): Getting space with id=%d", space_id)
    with closing(
        sqlite3.connect(get_sqlite_shared_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT id, org_id, name, summary, archived, datasource_type, datasource_configs, space_type, created_at, updated_at FROM spaces WHERE id = ? AND org_id = ?",
            (space_id, org_id),
        )
        row = cursor.fetchone()
        return _format_space(row) if row else None

def is_space_empty(space: SpaceKey) -> bool:
    """Check if a space has any docs or not."""
    docs = list_documents(space)
    return len(docs) == 0
