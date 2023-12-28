"""Functions for utilising storage."""

import logging as log
import os
import shutil
import time
from contextlib import suppress
from enum import Enum
from threading import Timer

from ..config import ENV_VAR_DOCQ_DATA, OrganisationFeatureType, SpaceType
from ..domain import SpaceKey


class _StoreSubdir(Enum):
    """Storage Subdirectories."""

    SQLITE = "sqlite"
    INDEX = "index"
    UPLOAD = "upload"
    MODELS = "models"


class _SqliteFilename(Enum):
    """SQLite filenames."""

    USAGE = "usage.db"
    SYSTEM = "system.db"


HISTORY_TABLE_NAME = "history_{feature}"
HISTORY_THREAD_TABLE_NAME = "history_thread_{feature}"
INACTIVITY_THRESHOLD = 60 * 60 * 2 * 24  # 1 day
CLEANUP_FREQUENCY = 60 * 60 * 1  # 1 hour


def _get_path(store: _StoreSubdir, type_: SpaceType, subtype: str = None, filename: str = None) -> str:
    log.debug("_get_path() - store: %s, type_: %s, subtype: %s, filename: %s", store, type_, subtype, filename)
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


def get_models_dir(model_group_key: str, makedir: bool = True) -> str:
    """Get directory where local models are stored."""

    dir_ = os.path.join(os.environ[ENV_VAR_DOCQ_DATA], _StoreSubdir.MODELS.value, model_group_key)

    if makedir:
        os.makedirs(dir_, exist_ok=True)
    return dir_


def get_upload_dir(space: SpaceKey) -> str:
    """Get the upload directory for a space."""
    return _get_path(
        store=_StoreSubdir.UPLOAD, type_=space.type_, subtype=os.path.join(str(space.org_id), str(space.id_))
    )


def get_upload_file(space: SpaceKey, filename: str) -> str:
    """Get the uploaded file for a space."""
    return _get_path(
        store=_StoreSubdir.UPLOAD,
        type_=space.type_,
        subtype=os.path.join(str(space.org_id), str(space.id_)),
        filename=filename,
    )


def get_index_dir(space: SpaceKey) -> str:
    """Get the index directory for a space."""
    return _get_path(
        store=_StoreSubdir.INDEX, type_=space.type_, subtype=os.path.join(str(space.org_id), str(space.id_))
    )


def get_sqlite_usage_file(id_: int) -> str:
    """Get the SQLite file for storing usage related data. All usage related data is segregated by user."""
    return _get_path(
        store=_StoreSubdir.SQLITE, type_=SpaceType.PERSONAL, subtype=str(id_), filename=_SqliteFilename.USAGE.value
    )


def get_public_sqlite_usage_file(id_: str) -> str:
    """Get the SQLite file for storing usage related data for public spaces."""
    return _get_path(
        store=_StoreSubdir.SQLITE, type_=SpaceType.PUBLIC, subtype=id_, filename=_SqliteFilename.USAGE.value
    )


def get_sqlite_system_file() -> str:
    """Get the SQLite file for storing space related data."""
    return _get_path(store=_StoreSubdir.SQLITE, type_=SpaceType.SHARED, filename=_SqliteFilename.SYSTEM.value)


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

    public_session_data_dir = _get_path(_StoreSubdir.SQLITE, SpaceType.PUBLIC)
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
