"""Functions to manage spaces."""

import json
import logging as log
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List

from llama_index import Document, GPTVectorStoreIndex

from docq.access_control.main import SpaceAccessor, SpaceAccessType

from .config import SpaceType
from .data_source.list import SpaceDataSources
from .domain import DocumentListItem, SpaceKey
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


def _create_index(documents: List[Document]) -> GPTVectorStoreIndex:
    # Use default storage and service context to initialise index purely for persisting
    return GPTVectorStoreIndex.from_documents(
        documents, storage_context=_get_default_storage_context(), service_context=_get_service_context()
    )


def _persist_index(index: GPTVectorStoreIndex, space: SpaceKey) -> None:
    index.storage_context.persist(persist_dir=get_index_dir(space))


def reindex(space: SpaceKey) -> None:
    """Reindex documents in a space."""
    (ds_type, ds_configs) = get_space_data_source(space)

    try:
        log.debug("get datasource instance")
        documents = SpaceDataSources[ds_type].value.load(space, ds_configs)
        log.debug("docs to index, %s", len(documents))
        index = _create_index(documents)
        _persist_index(index, space)
    except Exception as e:
        log.exception("Error indexing space %s: %s", space, e)


def list_documents(space: SpaceKey) -> List[DocumentListItem]:
    """Return a list of tuples containing the filename, creation time, and size of each file in the space."""
    (ds_type, ds_configs) = get_space_data_source(space)

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


def get_space_data_source(space: SpaceKey) -> tuple[str, dict]:
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
        (id_, org_id, name, summary, archived, ds_type, ds_configs, created_at, updated_at) = get_shared_space(
            space.id_, space.org_id
        )

    return ds_type, ds_configs


def get_shared_space(id_: int, org_id: int) -> tuple[int, int, str, str, bool, str, dict, datetime, datetime]:
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


def update_shared_space(
    id_: int,
    org_id: int,
    name: str = None,
    summary: str = None,
    archived: bool = False,
    datasource_type: str = None,
    datasource_configs: dict = None,
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
        log.debug("Created space with rowid: %d", rowid)
        space = SpaceKey(SpaceType.SHARED, rowid, org_id)

    reindex(space)

    return space


def list_shared_spaces(
    org_id: int, user_id: int = None
) -> list[tuple[int, str, str, bool, str, dict, datetime, datetime]]:
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
