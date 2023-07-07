import pytest
from docq.config import FeatureType, SpaceType
from docq.domain import FeatureKey, SpaceKey


@pytest.mark.parametrize(
    ("type_", "id_", "expected_str", "expected_value"),
    [
        (SpaceType.PERSONAL, 1234, "PERSONAL:1234", "PERSONAL_1234"),
        (SpaceType.SHARED, 9999, "SHARED:9999", "SHARED_9999"),
    ],
)
def test_space_key(type_, id_, expected_str, expected_value):
    key = SpaceKey(type_, id_)
    assert str(key) == expected_str
    assert key.value() == expected_value


@pytest.mark.parametrize(
    ("type_", "id_", "expected_str", "expected_value"),
    [
        (FeatureType.ASK_PERSONAL, 9876, "ASK_PERSONAL:9876", "ASK_PERSONAL_9876"),
        (FeatureType.ASK_SHARED, 9999, "ASK_SHARED:9999", "ASK_SHARED_9999"),
        (FeatureType.CHAT_PRIVATE, 8888, "CHAT_PRIVATE:8888", "CHAT_PRIVATE_8888"),
    ],
)
def test_feature_key(type_, id_, expected_str, expected_value):
    key = FeatureKey(type_, id_)
    assert str(key) == expected_str
    assert key.value() == expected_value
