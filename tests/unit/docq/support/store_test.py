"""Store module unit tests."""
import os
import tempfile
from typing import TypeVar

import pytest
from docq.config import FeatureType, SpaceType
from docq.domain import SpaceKey
from docq.support.store import (
    get_history_table_name,
    get_index_dir,
    get_sqlite_system_file,
    get_sqlite_usage_file,
    get_upload_dir,
    get_upload_file,
)

Self = TypeVar("Self", bound="TestGetPath")

DATA_DIR = os.path.join(tempfile.gettempdir(), "docq-data")


class TestGetPath:
    """Test get path."""
    @pytest.fixture(autouse=True)
    def _env(self: Self) -> None:
        os.environ["DOCQ_DATA"] = DATA_DIR

    @pytest.mark.parametrize(
        ("type_", "id_", "org_id", "expected"),
        [
            (SpaceType.SHARED, 88, 5555, DATA_DIR + "/upload/SHARED/5555/88"),
            (SpaceType.PERSONAL, 9999, 5555, DATA_DIR + "/upload/PERSONAL/9999"),
        ],
    )
    def test_get_upload_dir(self: Self, type_: SpaceType, id_: int, org_id: int, expected: str) -> None:
        """Test get upload dir."""
        assert get_upload_dir(SpaceKey(type_, id_, org_id)) == expected

    @pytest.mark.parametrize(
        ("type_", "id_", "org_id", "filename", "expected"),
        [
            (SpaceType.SHARED, 1, 234, "useful.pdf", DATA_DIR + "/upload/SHARED/234/1/useful.pdf"),
            (SpaceType.PERSONAL, 2, 234, "not-quite.jpeg", DATA_DIR + "/upload/PERSONAL/2/not-quite.jpeg"),
        ],
    )
    def test_get_upload_file(self: Self, type_: SpaceType, id_: int, org_id: int, filename: str, expected: str) -> None:
        """Test get upload file."""
        assert get_upload_file(SpaceKey(type_, id_, org_id), filename) == expected

    @pytest.mark.parametrize(
        ("type_", "id_", "org_id", "expected"),
        [
            (SpaceType.SHARED, 19, 345, DATA_DIR + "/index/SHARED/345/19"),
            (SpaceType.PERSONAL, 27, 345, DATA_DIR + "/index/PERSONAL/27"),
        ],
    )
    def test_get_index_dir(self: Self, type_: SpaceType, id_: int, org_id: int, expected: str) -> None:
        """Test get index dir."""
        assert get_index_dir(SpaceKey(type_, id_, org_id)) == expected

    @pytest.mark.parametrize(
        ("id_", "expected"),
        [
            (88, DATA_DIR + "/sqlite/PERSONAL/88/usage.db"),
            (9999, DATA_DIR + "/sqlite/PERSONAL/9999/usage.db"),
        ],
    )
    def test_get_sqlite_usage_file(self: Self, id_: int, expected: str) -> None:
        """Test get sqlite usage file."""
        assert get_sqlite_usage_file(id_) == expected

    def test_get_sqlite_system_file(self: Self) -> None:
        """Test get sqlite system file."""
        assert get_sqlite_system_file() == DATA_DIR + "/sqlite/SHARED/system.db"


@pytest.mark.parametrize(
    ("type_", "expected"),
    [
        (FeatureType.ASK_SHARED, "history_ask_shared"),
        (FeatureType.ASK_PERSONAL, "history_ask_personal"),
        (FeatureType.CHAT_PRIVATE, "history_chat_private"),
    ],
)
def test_get_history_table_name(type_: FeatureType, expected: str) -> None:
    """Test get history table name."""
    assert get_history_table_name(type_) == expected
