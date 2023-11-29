"""Test utilities."""
import json
import os

from docq import config, domain, manage_organisations, manage_users

from web.utils.constants import SessionKeyNameForAuth

TEST_FIXTURES = os.environ.get("TEST_FIXTURES_PATH", "tests/integration/fixtures")
DOCQ_DATA_KEY = config.ENV_VAR_DOCQ_DATA
TEST_FILE_PATH = "misc/test_files/integration_test.pdf"
TEST_FILE_NAME = "integration_test.pdf"
AI_MODEL_COLLECTION_NAME = os.environ.get("DOCQ_TEST_AI_MODEL_COLLECTION_NAME", "openai_latest")


def get_user() -> dict:
    """Get a test user."""
    with open(f"{TEST_FIXTURES}/test_user.json", "r") as f:
        return json.load(f)


def get_sample_file() -> bytes:
    """Read the test file pdf and return the data in bytes."""
    with open(TEST_FILE_PATH, "rb") as f:
        return f.read()


def get_features(user_id: int) -> dict[str, domain.FeatureKey]:
    """Get chat and ask features."""
    return {
        config.OrganisationFeatureType.ASK_PERSONAL.name: domain.FeatureKey(config.OrganisationFeatureType.ASK_PERSONAL, user_id),
        config.OrganisationFeatureType.ASK_SHARED.name: domain.FeatureKey(config.OrganisationFeatureType.ASK_SHARED, user_id),
        config.OrganisationFeatureType.CHAT_PRIVATE.name: domain.FeatureKey(config.OrganisationFeatureType.CHAT_PRIVATE, user_id)
    }


def get_auth_results(test_user: dict, user_id: int, selected_org_admin: bool = False) -> dict:
    """Authenticate a user and retrive auth results."""
    manage_users.set_user_as_verified(user_id)
    auth_result = manage_users.authenticate(**test_user)

    assert auth_result is not None, "Authentication failed"
    list_orgs = manage_organisations.list_organisations(user_id=auth_result[0])
    default_org_id = list_orgs[0][0] if list_orgs else None

    return {
        SessionKeyNameForAuth.ID.name: auth_result[0],
        SessionKeyNameForAuth.SELECTED_ORG_ID.name: default_org_id,
        SessionKeyNameForAuth.NAME.name: auth_result[1],
        SessionKeyNameForAuth.USERNAME.name: auth_result[3],
        SessionKeyNameForAuth.SUPER_ADMIN.name: auth_result[2],
        SessionKeyNameForAuth.SELECTED_ORG_ADMIN.name: selected_org_admin
    }

