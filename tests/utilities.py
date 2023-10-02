"""Test utilities."""
import json
import os

from docq import config, domain, manage_organisations, manage_users

from web.utils.constants import SessionKeyNameForAuth

TEST_FIXTURES = os.environ.get("TEST_FIXTURES_PATH", "tests/integration/fixtures")
DOCQ_DATA_KEY = config.ENV_VAR_DOCQ_DATA
TEST_FILE_PATH = "misc/test_files/integration_test.pdf"
TEST_FILE_NAME = "integration_test.pdf"
TEST_ENV_FILE_PATH = "tests/integration/.env"


def get_user() -> dict:
    """Get a test user."""
    with open(f"{TEST_FIXTURES}/test_user.json", "r") as f:
        return json.load(f)


def get_sample_file() -> bytes:
    """Read the test file pdf and return the data in bytes."""
    with open(TEST_FILE_PATH, "rb") as f:
        return f.read()


def setup_env() -> None:
    """Get test env."""
    if os.path.exists(TEST_ENV_FILE_PATH):
        with open(TEST_ENV_FILE_PATH, "r") as f:
            for line in f.readlines():
                print(f"\x1b[32mDebug env line: {line}\x1b[0m")
                key, value = line.split("=")
                print(f"\x1b[32mDebug env setting key: {key}, to value:{value}\x1b[0m")
                os.environ[key.strip()] = value.strip()
    # assert os.environ.get(DOCQ_DATA_KEY), f"Environment variable {DOCQ_DATA_KEY} not set."
    # assert os.environ.get(config.ENV_VAR_OPENAI_API_KEY), f"Environment variable {config.ENV_VAR_OPENAI_API_KEY} not set."
    # assert os.environ.get(config.ENV_VAR_DOCQ_COOKIE_HMAC_SECRET_KEY), f"Environment variable {config.ENV_VAR_DOCQ_COOKIE_HMAC_SECRET_KEY} not set."
    # assert "test" in os.environ[DOCQ_DATA_KEY].lower(), f"""
    # Environment variable {DOCQ_DATA_KEY} should contain 'test' in its value.
    # e.g. {DOCQ_DATA_KEY}=/path/to/docqai/test/data or {DOCQ_DATA_KEY}=/path/to/test-data
    # This is to prevent accidental deletion of data in production
    # """


def get_features(user_id: int) -> dict[str, domain.FeatureKey]:
    """Get chat and ask features."""
    return {
        config.FeatureType.ASK_PERSONAL.name: domain.FeatureKey(config.FeatureType.ASK_PERSONAL, user_id),
        config.FeatureType.ASK_SHARED.name: domain.FeatureKey(config.FeatureType.ASK_SHARED, user_id),
        config.FeatureType.CHAT_PRIVATE.name: domain.FeatureKey(config.FeatureType.CHAT_PRIVATE, user_id)
    }


def get_auth_results(test_user: dict, selected_org_admin: bool = False) -> dict:
    """Authenticate a user and retrive auth results."""
    auth_result = manage_users.authenticate(**test_user)
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

