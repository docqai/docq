import pytest
from docq.config import FeatureType, SpaceType
from docq.domain import FeatureKey, SpaceKey


@pytest.mark.parametrize(
    ("type_", "id_", "expected_str", "expected_value"),
    [
        (SpaceType.PERSONAL, 1234, "personal:1234", "personal_1234"),
        (SpaceType.SHARED, 9999, "shared:9999", "shared_9999"),
    ],
)
def test_space_key(type_, id_, expected_str, expected_value):
    key = SpaceKey(type_, id_)
    assert str(key) == expected_str
    assert key.value() == expected_value


@pytest.mark.parametrize(
    ("type_", "id_", "expected_str", "expected_value"),
    [
        (FeatureType.ASK_PERSONAL, 9876, "ask_personal:9876", "ask_personal_9876"),
        (FeatureType.ASK_SHARED, 9999, "ask_shared:9999", "ask_shared_9999"),
        (FeatureType.CHAT_PRIVATE, 8888, "chat_private:8888", "chat_private_8888"),
    ],
)
def test_feature_key(type_, id_, expected_str, expected_value):
    key = FeatureKey(type_, id_)
    assert str(key) == expected_str
    assert key.value() == expected_value
