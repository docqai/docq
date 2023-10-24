"""Functions to manage spaces."""

import json
import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Optional, Tuple

from llama_index import Document, DocumentSummaryIndex, VectorStoreIndex
from llama_index.indices.base import BaseIndex

from .access_control.main import SpaceAccessor, SpaceAccessType
from .config import SpaceType
from .data_source.list import SpaceDataSources
from .domain import DocumentListItem, SpaceKey
from .model_selection.main import ModelUsageSettingsCollection, get_saved_model_settings_collection
from .support.llm import _get_default_storage_context, _get_service_context
from .support.store import get_index_dir, get_sqlite_system_file

SQL_CREATE_SPACES_TABLE = """
CREATE TABLE IF NOT EXISTS spaces (
    id INTEGER PRIMARY KEY,
    org_id INTEGER NOT NULL,
    name TEXT UNIQUE,
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


def _init() -> None:
    """Initialize the database."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(SQL_CREATE_SPACES_TABLE)
        cursor.execute(SQL_CREATE_SPACE_ACCESS_TABLE)
        connection.commit()


def _create_index(
    documents: List[Document], model_settings_collection: ModelUsageSettingsCollection
) -> VectorStoreIndex:
    # Use default storage and service context to initialise index purely for persisting
    return VectorStoreIndex.from_documents(
        documents,
        storage_context=_get_default_storage_context(),
        service_context=_get_service_context(model_settings_collection),
    )


def _create_document_summary_index(
    documents: List[Document], model_settings_collection: ModelUsageSettingsCollection
) -> DocumentSummaryIndex:
    """Create a an index of summaries for each document."""
    return DocumentSummaryIndex.from_documents(
        documents,
        storage_context=_get_default_storage_context(),
        service_context=_get_service_context(model_settings_collection),
    )


def _persist_index(index: BaseIndex, space: SpaceKey) -> None:
    """Persist an Space datasource index to disk."""
    index.storage_context.persist(persist_dir=get_index_dir(space))


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
        log.debug("reindex(): docs to index, %s", len(documents))
        log.debug("reindex(): first doc metadata: %s", documents[0].metadata)
        log.debug("reindex(): first doc text: %s", documents[0].text)
        # index = _create_index(documents, saved_model_settings)
        # _persist_index(index, space)
        summary_index = _create_document_summary_index(documents, saved_model_settings)
        _persist_index(summary_index, space)
    except Exception as e:
        if e.__str__().__contains__("No files found"):
            log.info("Reindex skipped. No documents found in space '%s'", space)
        else:
            log.exception("Error indexing space '%s'. Error: %s", space, e)
    finally:
        log.debug("reindex(): Complete")


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


def get_space_data_source(space: SpaceKey) -> tuple[str, dict] | None:
    """Returns the data source type and configuration for the given space.

    Args:
        space (SpaceKey): The space to get the data source for.

    Returns:
        tuple[str, dict]: A tuple containing the data source type and configuration.
    """
    if space.type_ == SpaceType.PERSONAL:
        ds_type = "MANUAL_UPLOAD"
        ds_configs = {}
    else:
        shared_space = get_shared_space(space.id_, space.org_id)
        if shared_space is None:
            raise ValueError(f"No shared space found with id {space.id_} and org_id {space.org_id}")
        (_, _, _, _, _, ds_type, ds_configs, _, _) = shared_space

    return ds_type, ds_configs


def get_shared_space(id_: int, org_id: int) -> tuple[int, int, str, str, bool, str, dict, datetime, datetime] | None:
    """Get a shared space."""
    log.debug("get_shared_space(): Getting space with id=%d", id_)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT id, org_id, name, summary, archived, datasource_type, datasource_configs, created_at, updated_at FROM spaces WHERE id = ? AND org_id = ?",
            (id_, org_id),
        )
        row = cursor.fetchone()
        return (
            (row[0], row[1], row[2], row[3], bool(row[4]), row[5], json.loads(row[6]), row[7], row[8]) if row else None
        )


def get_shared_spaces(space_ids: List[int]) -> List[Tuple[int, int, str, str, bool, str, dict, datetime, datetime]]:
    """Get a shared spaces by ids.

    Returns:
        list[tuple[int, int, str, str, bool, str, dict, datetime, datetime]] - [id, org_id, name, summary, archived, datasource_type, datasource_configs, created_at, updated_at]
    """
    log.debug("get_shared_spaces(): Getting space with ids=%s", space_ids)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        placeholders = ", ".join("?" * len(space_ids))
        query = "SELECT id, org_id, name, summary, archived, datasource_type, datasource_configs, created_at, updated_at FROM spaces WHERE id IN ({})".format(
            placeholders
        )
        cursor.execute(query, space_ids)
        rows = cursor.fetchall()
        return [
            (row[0], row[1], row[2], row[3], bool(row[4]), row[5], json.loads(row[6]), row[7], row[8]) for row in rows
        ]


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
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(query, params)
        connection.commit()
        log.debug("Updated space %d", id_)
        return True


def create_shared_space(
    org_id: int, name: str, summary: str, datasource_type: str, datasource_configs: dict
) -> SpaceKey:
    """Create a shared space."""
    params = (
        org_id,
        name,
        summary,
        datasource_type,
        json.dumps(datasource_configs),
    )
    log.debug("Creating space with params: %s", params)
    rowid = None
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO spaces (org_id, name, summary, datasource_type, datasource_configs) VALUES (?, ?, ?, ?, ?)",
            params,
        )
        rowid = cursor.lastrowid
        connection.commit()
        if rowid is None:
            raise ValueError("Failed to create space")
        log.debug("Created space with rowid: %d", rowid)
        space = SpaceKey(SpaceType.SHARED, rowid, org_id)

    reindex(space)

    return space


def list_shared_spaces(
    org_id: int, user_id: Optional[int] = None
) -> list[tuple[int, int, str, str, bool, str, dict, datetime, datetime]]:
    """List all shared spaces."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            "SELECT id, org_id, name, summary, archived, datasource_type, datasource_configs, created_at, updated_at FROM spaces WHERE org_id = ? ORDER BY name",
            (org_id,),
        )
        rows = cursor.fetchall()
        return [
            (row[0], row[1], row[2], row[3], bool(row[4]), row[5], json.loads(row[6]), row[7], row[8]) for row in rows
        ]


def list_public_spaces(space_group_id: int) -> list[tuple[int, int, str, str, bool, str, dict, datetime, datetime]]:
    """List all public spaces from a given space group."""
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
    ) as connection, closing(connection.cursor()) as cursor:
        cursor.execute(
            """
            SELECT s.id, s.org_id, s.name, s.summary, s.archived, s.datasource_type, s.datasource_configs, s.created_at, s.updated_at
            FROM spaces s
            JOIN space_group_members c
            LEFT JOIN space_access sa ON s.id = sa.space_id
            WHERE c.group_id = ? AND c.space_id = s.id
            AND sa.access_type = ?
            ORDER BY name
            """,
            (space_group_id, SpaceAccessType.PUBLIC.name),
        )
        rows = cursor.fetchall()
        return [
            (row[0], row[1], row[2], row[3], bool(row[4]), row[5], json.loads(row[6]), row[7], row[8]) for row in rows
        ]


def get_shared_space_permissions(id_: int, org_id: int) -> List[SpaceAccessor]:
    """Get the permissions for a shared space."""
    log.debug("get_shared_space_permissions(): Getting permissions for space with id=%d", id_)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
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


def update_shared_space_permissions(id_: int, accessors: List[SpaceAccessor]) -> bool:
    """Update the permissions for a shared space."""
    log.debug("update_shared_space_permissions(): Updating permissions for space with id=%d", id_)
    with closing(
        sqlite3.connect(get_sqlite_system_file(), detect_types=sqlite3.PARSE_DECLTYPES)
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
