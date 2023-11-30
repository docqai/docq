"""Domain tests."""
import pytest
from docq.config import OrganisationFeatureType, SpaceType
from docq.domain import FeatureKey, SpaceKey


@pytest.mark.parametrize(
    ("type_", "id_", "org_id", "expected_str", "expected_value"),
    [
        (SpaceType.SHARED, 9999, 6789, "SHARED:6789:9999", "SHARED_6789_9999"),
    ],
)
def test_space_key(type_: SpaceType, id_: int, org_id: int, expected_str: str, expected_value: str) -> None:
    """Test space key."""
    key = SpaceKey(type_, id_, org_id)
    assert str(key) == expected_str
    assert key.value() == expected_value


@pytest.mark.parametrize(
    ("type_", "id_", "expected_str", "expected_value"),
    [
        (OrganisationFeatureType.ASK_SHARED, 9999, "ASK_SHARED:9999", "ASK_SHARED_9999"),
        (OrganisationFeatureType.CHAT_PRIVATE, 8888, "CHAT_PRIVATE:8888", "CHAT_PRIVATE_8888"),
    ],
)
def test_feature_key(type_: OrganisationFeatureType, id_: int, expected_str: str, expected_value: str) -> None:
    """Test feature key."""
    key = FeatureKey(type_, id_)
    assert str(key) == expected_str
    assert key.value() == expected_value
