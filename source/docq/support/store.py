"""Functions for utilising storage."""

import logging as log
import os
from enum import Enum

from ..config import ENV_VAR_DOCQ_DATA, FeatureType, SpaceType
from ..domain import SpaceKey


class _StoreSubdir(Enum):
    """Storage Subdirectories."""

    SQLITE = "sqlite"
    INDEX = "index"
    UPLOAD = "upload"


class _SqliteFilename(Enum):
    """SQLite filenames."""

    USAGE = "usage.db"
    SYSTEM = "system.db"


HISTORY_TABLE_NAME = "history_{feature}"
HISTORY_THREAD_TABLE_NAME = "history_thread_{feature}"


def _get_path(store: _StoreSubdir, type_: SpaceType, subtype: str = None, filename: str = None) -> str:
    dir_ = (
        os.path.join(os.environ[ENV_VAR_DOCQ_DATA], store.value, type_.name, subtype)
        if subtype
        else os.path.join(os.environ[ENV_VAR_DOCQ_DATA], store.value, type_.name)
    )
    os.makedirs(dir_, exist_ok=True)
    if filename:
        file_ = os.path.join(dir_, filename)
        log.debug("File: %s", file_)
        return file_
    else:
        log.debug("Dir: %s", dir_)
        return dir_


def get_upload_dir(space: SpaceKey) -> str:
    """Get the upload directory for a space."""
    return _get_path(_StoreSubdir.UPLOAD, space.type_, str(space.id_))


def get_upload_file(space: SpaceKey, filename: str) -> str:
    """Get the uploaded file for a space."""
    return _get_path(_StoreSubdir.UPLOAD, space.type_, str(space.id_), filename)


def get_index_dir(space: SpaceKey) -> str:
    """Get the index directory for a space."""
    return _get_path(_StoreSubdir.INDEX, space.type_, str(space.id_))


def get_sqlite_usage_file(id_: int) -> str:
    """Get the SQLite file for storing usage related data."""
    return _get_path(_StoreSubdir.SQLITE, SpaceType.PERSONAL, str(id_), filename=_SqliteFilename.USAGE.value)


def get_sqlite_system_file() -> str:
    """Get the SQLite file for storing space related data."""
    return _get_path(_StoreSubdir.SQLITE, SpaceType.SHARED, filename=_SqliteFilename.SYSTEM.value)


def get_history_table_name(type_: FeatureType) -> str:
    """Get the history table name for a feature."""
    # Note that because it's used for database table name, `lower()` is used to ensure it's all lowercase.
    return HISTORY_TABLE_NAME.format(feature=type_.name.lower())


def get_history_thread_table_name(type_: FeatureType) -> str:
    """Get the history table name for a feature."""
    # Note that because it's used for database table name, `lower()` is used to ensure it's all lowercase.
    return HISTORY_THREAD_TABLE_NAME.format(feature=type_.name.lower())
