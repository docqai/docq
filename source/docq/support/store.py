"""Functions for utilising storage."""

import logging as log
import os
import shutil
import time
from contextlib import suppress
from enum import Enum
from threading import Timer
from typing import Optional

from ..config import ENV_VAR_DOCQ_DATA, OrganisationFeatureType, SpaceType
from ..domain import SpaceKey


class _StoreDir(Enum):
    """Storage directories. This is based on the type and format of storage system used like SQLite, index, and models."""

    SQLITE = "sqlite"
    INDEX = "index"
    UPLOAD = "upload"
    MODELS = "models"


class _SqliteFilename(Enum):
    """SQLite filenames. Files are separated based on the type of data being stored."""

    USAGE = "usage.db"
    SYSTEM = "system.db"

class _DataScope(Enum):
    """The data access scopes used to partition data persistance. Note scoped by ownership not sharing and access.

    This enum should not be used as a type discriminator on data models directly. Rather should be mapped for a model specific type enum.
    Example: SpaceType should be napped to a DataScope when picking index and DB file locations.
    """
    PERSONAL = "personal"
    """Data that is owned by a user. Usage data is always at this scope."""
    ORG = "org"
    """Data that's owned by an organisation and applies to all users within the org."""
    GLOBAL = "global"
    """Data that applies across org boundaries and not owned by any single organisation."""
    PUBLIC = "public"
    """Data that associated with anonymous users like interaction with a public chat bot."""
    SHARED = "shared"
    """DEPRECATED. don't use for new features. Here for backwards compatibility."""
    THREAD = "thread"
    """DEPRECATED. don't use for new features. Here for backwards compatibility."""


HISTORY_TABLE_NAME = "history_{feature}"
HISTORY_THREAD_TABLE_NAME = "history_thread_{feature}"

# These variable are used to clean up public chat history.
INACTIVITY_THRESHOLD = 60 * 60 * 2 * 24  # 1 day
CLEANUP_FREQUENCY = 60 * 60 * 1  # 1 hour


def _get_path(
    store: _StoreDir, data_scope: _DataScope, subtype: Optional[str] = None, filename: Optional[str] = None
) -> str:
    """The params are used to consistently build a path for things that require a file path like SQLite.

    Using this function directly should be avoided. Create wrapper function for specific use cases and call those from within app code.

    Note: data_scope.value is converted to upper case to maintain backward compatibility.

    Args:
        store: The store dir.
        data_scope: The data scope dir.
        subtype: (optional) subtype if data scope requires further partitioning.
        filename: (optional) The filename.
    """
    log.debug(
        "_get_path() - store: %s, data_scope: %s, subtype: %s, filename: %s", store, data_scope, subtype, filename
    )
    dir_ = (
        os.path.join(os.environ[ENV_VAR_DOCQ_DATA], store.value, data_scope.value.upper(), subtype)
        if subtype
        else os.path.join(os.environ[ENV_VAR_DOCQ_DATA], store.value, data_scope.value.upper())
    )
    os.makedirs(dir_, exist_ok=True)
    if filename:
        file_ = os.path.join(dir_, filename)
        log.debug("File: %s", file_)
        return file_
    else:
        log.debug("Dir: %s", dir_)
        return dir_


def get_models_dir(model_group_key: str, makedir: bool = True) -> str:
    """Get directory where local models are stored."""
    dir_ = os.path.join(os.environ[ENV_VAR_DOCQ_DATA], _StoreDir.MODELS.value, model_group_key)

    if makedir:
        os.makedirs(dir_, exist_ok=True)
    return dir_


def get_upload_dir(space: SpaceKey) -> str:
    """Get the upload directory for a space."""
    return _get_path(
        store=_StoreDir.UPLOAD,
        data_scope=_map_space_type_to_datascope(space.type_),
        subtype=os.path.join(str(space.org_id), str(space.id_)),
    )


def get_upload_file(space: SpaceKey, filename: str) -> str:
    """Get the uploaded file for a space."""
    return _get_path(
        store=_StoreDir.UPLOAD,
        data_scope=_map_space_type_to_datascope(space.type_),
        subtype=os.path.join(str(space.org_id), str(space.id_)),
        filename=filename,
    )


def _map_space_type_to_datascope(space_type: SpaceType) -> _DataScope:
    """Map space type to data scope."""
    data_scope = None
    if space_type == SpaceType.PERSONAL:
        data_scope = _DataScope.PERSONAL
    elif space_type == SpaceType.SHARED:
        data_scope = _DataScope.SHARED  # TODO: switch to DataScope.ORG. this requires data migration scripts.
    elif space_type == SpaceType.PUBLIC:
        data_scope = _DataScope.PUBLIC
    elif space_type == SpaceType.THREAD:
        data_scope = _DataScope.THREAD  # TODO: migrate to DataScope.PERSONAL. This requires data migration scripts.
    else:
        raise ValueError(f"Invalid space type: {space_type}")
    return data_scope

def get_index_dir(space: SpaceKey) -> str:
    """Get the index directory for a space."""
    _data_scope = _map_space_type_to_datascope(space.type_)
    return _get_path(
        store=_StoreDir.INDEX, data_scope=_data_scope, subtype=os.path.join(str(space.org_id), str(space.id_))
    )


def get_sqlite_usage_file(id_: int) -> str:
    """Get the SQLite file for storing usage related data. All usage related data is segregated by user i.e. inherently PERSONAL."""
    return _get_path(
        store=_StoreDir.SQLITE, data_scope=_DataScope.PERSONAL, subtype=str(id_), filename=_SqliteFilename.USAGE.value
    )


def get_public_sqlite_usage_file(id_: str) -> str:
    """Get the SQLite file for storing usage related data for public spaces."""
    return _get_path(
        store=_StoreDir.SQLITE, data_scope=_DataScope.PUBLIC, subtype=id_, filename=_SqliteFilename.USAGE.value
    )


def get_sqlite_global_system_file() -> str:
    """Get the SQLite file for storing global scoped system data."""
    # TODO: change to use DataScope.SYSTEM. Requires migration scripts.
    return _get_path(store=_StoreDir.SQLITE, data_scope=_DataScope.SHARED, filename=_SqliteFilename.SYSTEM.value)

def get_sqlite_user_system_file() -> str:
    """Get the SQLite file for storing user scoped system data."""
    return _get_path(store=_StoreDir.SQLITE, data_scope=_DataScope.PERSONAL, filename=_SqliteFilename.SYSTEM.value)

def get_sqlite_org_system_file() -> str:
    """Get the SQLite file for the storing org scoped system data."""
    return _get_path(store=_StoreDir.SQLITE, data_scope=_DataScope.ORG, filename=_SqliteFilename.SYSTEM.value)


def get_history_table_name(type_: OrganisationFeatureType) -> str:
    """Get the history table name for a feature."""
    # Note that because it's used for database table name, `lower()` is used to ensure it's all lowercase.
    return HISTORY_TABLE_NAME.format(feature=type_.name.lower())


def get_history_thread_table_name(type_: OrganisationFeatureType) -> str:
    """Get the history table name for a feature."""
    # Note that because it's used for database table name, `lower()` is used to ensure it's all lowercase.
    return HISTORY_THREAD_TABLE_NAME.format(feature=type_.name.lower())


def _clean_public_chat_history() -> None:
    """Clean public chat history."""
    scheduler = Timer(CLEANUP_FREQUENCY, _clean_public_chat_history)
    scheduler.daemon = True
    scheduler.start()

    public_session_data_dir = _get_path(_StoreDir.SQLITE, _DataScope.PUBLIC)
    current_time = int(time.time())

    for dir_ in os.listdir(public_session_data_dir):
        dir_path = os.path.join(public_session_data_dir, dir_)
        last_activity = os.path.getmtime(dir_path)
        time_diffence = current_time - last_activity
        if time_diffence > INACTIVITY_THRESHOLD:
            with suppress(FileNotFoundError):
                log.info("Removing public chat history for session %s", dir_)
                shutil.rmtree(dir_path)


def _init() -> None:
    """Initialise storage."""
    _clean_public_chat_history()
