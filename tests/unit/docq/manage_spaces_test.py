"""Tests for docq.manage_spaces module."""
import json
import logging as log
import sqlite3
import tempfile
from contextlib import closing
from typing import Generator, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest
from docq.access_control.main import SpaceAccessor, SpaceAccessType
from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.model_selection.main import ModelCapability, get_model_settings_collection
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.schema import Document

TEST_ORG_ID = 1000

@pytest.fixture(scope="session")
def manage_spaces_test_dir() -> Generator:
    """Create a temporary directory for testing."""
    from docq.manage_spaces import _init
    log.info("Setup manage spaces test.")

    with tempfile.TemporaryDirectory() as temp_dir, patch(
        "docq.manage_spaces.get_sqlite_shared_system_file"
    ) as mock_get_sqlite_shared_system_file:
        sqlite_system_file = f"{temp_dir}/sql_system.db"
        mock_get_sqlite_shared_system_file.return_value = sqlite_system_file

        _init()

        yield temp_dir, sqlite_system_file, mock_get_sqlite_shared_system_file

    log.info("Teardown manage spaces test.")


def insert_test_space(sqlite_system_file: str, name: str, space_type: Optional[str] = None) -> Optional[int]:
    """Insert a test space."""
    if space_type is None:
        space_type = SpaceType.SHARED.name
    with closing(sqlite3.connect(sqlite_system_file)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("INSERT INTO spaces (org_id, name, space_type, summary, datasource_type, datasource_configs) VALUES (?, ?, ?, ?, ?, ?)", (TEST_ORG_ID, name, space_type, "test space description", "test ds_type", json.dumps({"test": "test"})))
        space_id = cursor.lastrowid
        connection.commit()

    return space_id


def test_db_init(manage_spaces_test_dir: tuple) -> None:
    """Test db init."""
    with closing(sqlite3.connect(manage_spaces_test_dir[1])) as connection, closing(connection.cursor()) as cursor:
        sql_select = "SELECT name FROM sqlite_master WHERE type='table' AND name = ?"
        tables = [("spaces",), ("space_access",)]

        for table in tables:
            cursor.execute(sql_select, table)
            result = cursor.fetchone()
            assert result is not None, f"Table {table} not found."


@patch("docq.manage_spaces._get_default_storage_context")
@patch("docq.manage_spaces._get_service_context")
def test_create_index(get_service_context: MagicMock, get_default_storage_context: MagicMock) -> None:
    """Test create index."""
    from docq.manage_spaces import _create_vector_index

    with patch("docq.manage_spaces.VectorStoreIndex", Mock(from_documents=MagicMock())):
        documents = Mock([Document])
        model_settings_collection = Mock()
        mocked_model_usage_settings = Mock()
        mocked_model_usage_settings.additional_args = {"arg1": "value1", "arg2": "value2"}
        model_settings_collection.model_usage_settings = {ModelCapability.CHAT: mocked_model_usage_settings}
        _create_vector_index(documents, model_settings_collection)

        get_service_context.assert_called_once_with(model_settings_collection)
        get_default_storage_context.assert_called_once()


def test_reindex_vector_index() -> None:
    """Test reindex."""
    from docq.manage_spaces import reindex

    with patch("docq.manage_indices._persist_index") as mock_persist_index, patch(
        "docq.manage_indices._create_vector_index"
    ) as mock_create_vector_index, patch(
        "docq.manage_spaces.get_space_data_source"
    ) as mock_get_space_data_source, patch(
        "docq.data_source.manual_upload.ManualUpload.load"
    ) as mock_ManualUpload_load, patch(  # noqa: N806
        "docq.manage_spaces.get_saved_model_settings_collection"  # note the reference to the file where the function is called, not defined.
    ) as mock_get_saved_model_settings_collection:  # noqa: N806
        # mock_index = Mock(DocumentSummaryIndex)
        # mock_create_document_summary_index.return_value = mock_index

        mock_vector_index = Mock(VectorStoreIndex)
        mock_create_vector_index.return_value = mock_vector_index

        mock_get_space_data_source.return_value = ("MANUAL_UPLOAD", {})

        mock_ManualUpload_load.return_value = [
            Document(doc_id="testid", text="test", extra_info={"source_uri": "https://example.com}"})
        ]

        arg_space_key = SpaceKey(SpaceType.SHARED, 1234, 4567, "this is a test space with mocked data")

        mock_get_saved_model_settings_collection.return_value = get_model_settings_collection("openai_latest")
        # print({mock_get_saved_model_settings_collection.return_value.__str__()})
        reindex(arg_space_key)

        mock_persist_index.assert_called_once_with(mock_vector_index, arg_space_key)


@patch("docq.manage_indices.get_index_dir")
def test_persist_index(get_index_dir: MagicMock) -> None:
    """Test persist index."""
    from docq.manage_indices import _persist_index

    def _persist (persist_dir: str) -> None:
        with open(persist_dir, "w") as f:
            f.write("test")

    index = Mock(storage_context=Mock(persist=_persist))
    space = Mock()
    with tempfile.NamedTemporaryFile() as temp_file:
        get_index_dir.return_value = temp_file.name
        _persist_index(index, space)

        assert temp_file.read() == b"test"
        get_index_dir.assert_called_once_with(space)


def test_get_shared_space(manage_spaces_test_dir: tuple) -> None:
    """Test get shared space."""
    from docq.manage_spaces import get_shared_space

    sqlite_system_file = manage_spaces_test_dir[1]
    space_id = insert_test_space(sqlite_system_file, "get_shared_space test")

    assert space_id is not None, "Space id not found."

    space = get_shared_space(space_id, TEST_ORG_ID)

    assert space is not None, "Space not found."
    assert space[0] == space_id, "Space id mismatch."


def test_get_shared_spaces(manage_spaces_test_dir: tuple) -> None:
    """Test get shared spaces."""
    from docq.manage_spaces import get_shared_spaces

    sqlite_system_file = manage_spaces_test_dir[1]
    space_id1 = insert_test_space(sqlite_system_file, "get_shared_spaces test 1")
    space_id2 = insert_test_space(sqlite_system_file, "get_shared_spaces test 2")

    assert space_id1 is not None, "Sample space_id 1 not found."
    assert space_id2 is not None, "Sample space_id 2 not found."

    spaces = get_shared_spaces([space_id1, space_id2])
    assert len(spaces) == 2, f"Expected 2 spaces, got {len(spaces)}."


def test_update_shared_space(manage_spaces_test_dir: tuple) -> None:
    """Test update shared space."""
    from docq.manage_spaces import update_shared_space

    sqlite_system_file = manage_spaces_test_dir[1]
    space_id = insert_test_space(sqlite_system_file, "update_shared_space test")
    space_name_updated = "update_shared_space test updated"

    assert space_id is not None, "Sample space id not found."

    update_space = update_shared_space(
        space_id,
        TEST_ORG_ID,
        name=space_name_updated,
        summary="test summary updated",
        datasource_type="test ds_type updated",
        datasource_configs={"test": "test updated"},
    )

    assert update_space, "Update failed."
    with closing(sqlite3.connect(sqlite_system_file)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT name FROM spaces WHERE id = ?", (space_id,))
        result = cursor.fetchone()
        assert result is not None, "Space not found."
        assert result[0] == space_name_updated, "Space name mismatch."


def test_create_shared_space(manage_spaces_test_dir: tuple) -> None:
    """Test create shared space."""
    from docq.manage_spaces import create_shared_space

    sqlite_system_file = manage_spaces_test_dir[1]
    space_name = "create_shared_space test"
    space_summary = "create_shared_space test summary"
    space_datasource_type = "create_shared_space test ds_type"
    space_datasource_configs = {"create_shared_space test": "create_shared_space test"}

    with patch("docq.manage_spaces.reindex") as reindex:
        space = create_shared_space(
            TEST_ORG_ID,
            space_name,
            space_summary,
            space_datasource_type,
            space_datasource_configs,
        )

    assert space is not None, "Space not found."
    with closing(sqlite3.connect(sqlite_system_file)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT name, summary, datasource_type, datasource_configs FROM spaces WHERE id = ?", (space.id_,))
        result = cursor.fetchone()
        assert result is not None, "Space not found."
        assert result[0] == space_name, "Space name mismatch."
        assert result[1] == space_summary, "Space summary mismatch."
        assert result[2] == space_datasource_type, "Space datasource_type mismatch."
        assert result[3] == json.dumps(space_datasource_configs), "Space datasource_configs mismatch."

    reindex.assert_called_once_with(space)


def test_create_thread_space(manage_spaces_test_dir: tuple) -> None:
    """Test create thread space."""
    sqlite_system_file = manage_spaces_test_dir[1]
    space_summary = "create_thread_space test summary"
    space_datasource_type = "create_thread_space test ds_type"
    test_thread_id = 1234

    def assert_pattern(thread_id: str, space_summary: str, thread_space_name: str) -> None:
        import re

        pattern = rf"Thread-{test_thread_id} {space_summary} \d+"
        assert (
            re.fullmatch(pattern, thread_space_name) is not None
        ), f"{thread_space_name} does not match pattern {pattern}"

    with patch("docq.manage_spaces.reindex") as reindex:
        from docq.manage_spaces import create_thread_space
        space = create_thread_space(
            TEST_ORG_ID,
            test_thread_id,
            space_summary,
            space_datasource_type,
        )

    assert space is not None, "Space not found."
    with closing(sqlite3.connect(sqlite_system_file)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("SELECT name, summary, datasource_type, datasource_configs FROM spaces WHERE id = ?", (space.id_,))
        result = cursor.fetchone()
        assert result is not None, "Space not found."
        # assert result[0] == f"Thread-{test_thread_id} {space_summary}", "Space name mismatch."
        assert result[1] == space_summary, "Space summary mismatch."
        assert result[2] == space_datasource_type, "Space datasource_type mismatch."
        assert_pattern(str(test_thread_id), space_summary, result[0])

    reindex.assert_called_once_with(space)


def test_get_thread_space() -> None:
    """Test get thread space."""
    space_summary = "get_thread_space test summary"
    space_datasource_type = "get_thread_space test ds_type"
    test_thread_id = 4321

    with patch("docq.manage_spaces.reindex") as reindex:
        from docq.manage_spaces import create_thread_space
        space = create_thread_space(
            TEST_ORG_ID,
            test_thread_id,
            space_summary,
            space_datasource_type,
        )

    assert space is not None, "Space not found."
    reindex.assert_called_once_with(space)

    from docq.manage_spaces import get_thread_space
    space_result = get_thread_space(TEST_ORG_ID, test_thread_id)

    assert space_result is not None, "Space not found."
    assert space_result.id_ == space.id_, "Space id mismatch."


def test_list_shared_space(manage_spaces_test_dir: tuple) -> None:
    """Test list shared space."""
    from docq.manage_spaces import list_shared_spaces

    sqlite_system_file = manage_spaces_test_dir[1]
    space_id1 = insert_test_space(sqlite_system_file, "list_shared_space test 1")
    space_id2 = insert_test_space(sqlite_system_file, "list_shared_space test 2")

    assert space_id1 is not None, "Sample space_id 1 not found."
    assert space_id2 is not None, "Sample space_id 2 not found."

    spaces = list_shared_spaces(TEST_ORG_ID)
    assert len(spaces) >= 2, f"Expected atleast 2 spaces, got {len(spaces)}."

    space_ids = [s[0] for s in spaces]
    assert space_id1 in space_ids, f"Space id {space_id1} not found."
    assert space_id2 in space_ids, f"Space id {space_id2} not found."


def test_list_public_spaces(manage_spaces_test_dir: tuple) -> None:
    """Test list public space."""
    from docq.manage_space_groups import _init
    from docq.manage_spaces import list_public_spaces

    sqlite_system_file = manage_spaces_test_dir[1]

    with patch("docq.manage_space_groups.get_sqlite_shared_system_file") as _get_sqlite_shared_system_file:
        _get_sqlite_shared_system_file.return_value = sqlite_system_file
        _init()

    space_id1 = insert_test_space(sqlite_system_file, "list_public_space test 1")
    space_id2 = insert_test_space(sqlite_system_file, "list_public_space test 2")

    assert space_id1 is not None, "Test list public spaces sample space_id 1 not found."
    assert space_id2 is not None, "Test list public spaces sample space_id 2 not found."

    with closing(sqlite3.connect(sqlite_system_file)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("INSERT INTO space_groups (org_id, name, summary) VALUES (?, ?, ?)", (TEST_ORG_ID, "test_group_1", "test group summary"))
        group_id = cursor.lastrowid
        cursor.execute("INSERT INTO space_group_members (group_id, space_id) VALUES (?, ?)", (group_id, space_id1))
        cursor.execute("INSERT INTO space_group_members (group_id, space_id) VALUES (?, ?)", (group_id, space_id2))
        cursor.execute("INSERT INTO space_access (space_id, access_type, accessor_id) VALUES (?, ?, ?)", (space_id1, SpaceAccessType.PUBLIC.name, group_id))
        cursor.execute("INSERT INTO space_access (space_id, access_type, accessor_id) VALUES (?, ?, ?)", (space_id2, SpaceAccessType.PUBLIC.name, group_id))
        connection.commit()

    assert group_id is not None, "Test list public spaces sample group_id not found."
    public_spaces = list_public_spaces(selected_org_id=TEST_ORG_ID, space_group_id=group_id)
    space_ids = [s[0] for s in public_spaces]
    assert space_id1 in space_ids, f"Space id {space_id1} not found."
    assert space_id2 in space_ids, f"Space id {space_id2} not found."
    assert len(public_spaces) == 2, f"Expected 2 spaces, got {len(public_spaces)}."


def test_get_shared_space_permissions(manage_spaces_test_dir: tuple) -> None:
    """Test get shared space permissions."""
    from docq import manage_user_groups, manage_users
    from docq.manage_spaces import get_shared_space_permissions

    sqlite_system_file = manage_spaces_test_dir[1]
    with patch("docq.manage_users.get_sqlite_shared_system_file") as p1, patch(
        "docq.manage_user_groups.get_sqlite_shared_system_file"
    ) as p2:
        p1.return_value = sqlite_system_file
        p2.return_value = sqlite_system_file
        manage_users._init()
        manage_user_groups._init()

    space_id = insert_test_space(sqlite_system_file, "get_shared_space_permissions test")
    ctrl_space_id = insert_test_space(sqlite_system_file, "get_shared_space_permissions ctrl test")

    assert space_id is not None, "Sample space id not found."
    assert ctrl_space_id is not None, "Sample ctrl space id not found."

    with closing(sqlite3.connect(sqlite_system_file)) as connection, closing(connection.cursor()) as cursor:
        cursor.execute("INSERT INTO users (username, password, fullname) VALUES (?, ?, ?)", ("test_user", "test_password", "test user"))
        user_id = cursor.lastrowid

        assert user_id is not None, "Sample user id not found."

        accessor = SpaceAccessor(SpaceAccessType.USER, user_id, "test_user")
        cursor.execute("INSERT INTO space_access (space_id, access_type, accessor_id) VALUES (?, ?, ?)", (space_id, accessor.type_.name, accessor.accessor_id))
        cursor.execute("INSERT INTO user_groups (org_id, name) VALUES (?, ?)", (TEST_ORG_ID, "test_user_group"))
        connection.commit()

        shared_space_permissions = get_shared_space_permissions(space_id, TEST_ORG_ID)

        assert shared_space_permissions is not None, "Shared space permissions not found."
        assert len(shared_space_permissions) == 1, f"Expected 1 space permission, got {len(shared_space_permissions)}."
        assert shared_space_permissions[0] == accessor, "Accessor mismatch."


def test_update_shared_space_permissions(manage_spaces_test_dir: tuple) -> None:
    """Test update shared space permissions."""
    from docq.manage_spaces import update_shared_space_permissions

    sqlite_system_file = manage_spaces_test_dir[1]
    space_id = insert_test_space(sqlite_system_file, "update_shared_space_permissions test user")


    assert space_id is not None, "Sample user space id not found."

    public_accessor = SpaceAccessor(SpaceAccessType.PUBLIC, space_id, "sample_public_accessor")
    user_accessor = SpaceAccessor(SpaceAccessType.USER, space_id, "sample_user_accessor")
    group_accessor = SpaceAccessor(SpaceAccessType.GROUP, space_id, "sample_group_accessor")

    updates = update_shared_space_permissions(space_id, [public_accessor, user_accessor, group_accessor])

    assert updates, "Update failed."
