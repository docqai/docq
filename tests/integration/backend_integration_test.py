"""Docq backend integration tests."""

import os
from contextlib import suppress
from shutil import rmtree

import pytest
from docq import config, domain, manage_documents, manage_settings, manage_users, run_queries, setup
from docq.model_selection.main import (
    ModelUsageSettingsCollection,
    get_saved_model_settings_collection,
)

from tests.utilities import (
    DOCQ_DATA_KEY,
    TEST_FILE_NAME,
    get_auth_results,
    get_features,
    get_sample_file,
    get_user,
)
from web.utils.constants import SessionKeyNameForAuth


@pytest.fixture(scope="session" , autouse=True)
def _setup_and_teardown() -> None:
    """Setup and teardown for each test."""
    print("Setup")
    # setup_env()
    setup.init()

    yield
    print("Teardown")
    with suppress(FileNotFoundError):
        rmtree(os.environ[DOCQ_DATA_KEY])


@pytest.fixture()
def test_user() -> dict:
    """Get a test user."""
    return get_user()

## User actions

# Create user
@pytest.fixture(autouse=True)
def _create_test_user(test_user: dict) -> None:
    """Create a test user."""
    with suppress(ValueError):
        manage_users.create_user(**test_user, verified=True)


# Login
@pytest.fixture()
def auth_results(test_user: dict) -> dict:
    """Authenticate the test user."""
    return get_auth_results(test_user)


@pytest.fixture()
def features(auth_results: dict) -> dict[str, domain.FeatureKey]:
    """Get available features."""
    return get_features(auth_results[SessionKeyNameForAuth.ID.name])


@pytest.fixture()
def personal_space(auth_results: dict) -> domain.SpaceKey:
    """Get personal space."""
    return domain.SpaceKey(
        domain.SpaceType.PERSONAL,
        auth_results[SessionKeyNameForAuth.ID.name],
        auth_results[SessionKeyNameForAuth.SELECTED_ORG_ID.name]
    )


@pytest.fixture()
def sample_file() -> bytes:
    """Get test file."""
    return get_sample_file()


# Upload file to a personal space
@pytest.fixture(autouse=True)
def _upload_test_file(sample_file: bytes, personal_space: domain.SpaceKey) -> None:
    """Upload a test file."""
    manage_documents.upload(TEST_FILE_NAME, sample_file, personal_space)


# Update organisation settings
@pytest.fixture(autouse=True)
def _update_organisation_settings(auth_results: dict) -> None:
    """Update organisation settings."""
    manage_settings.update_organisation_settings(
        {
            config.SystemSettingsKey.ENABLED_FEATURES.name: [
                f.name for f in config.FeatureType
            ],
            config.SystemSettingsKey.MODEL_COLLECTION.name: "openai_latest",
        },
        org_id=auth_results[SessionKeyNameForAuth.SELECTED_ORG_ID.name],
    )


# Get saved model settings
@pytest.fixture()
def saved_model_settings(auth_results: dict) -> ModelUsageSettingsCollection:
    """Get saved model settings."""
    return get_saved_model_settings_collection(
        auth_results[SessionKeyNameForAuth.SELECTED_ORG_ID.name]
    )


# Run tests
def test_user_exists(test_user: dict) -> None:
    """Test that user exists."""
    assert manage_users.authenticate(**test_user) is not None, "The test user should exist."


def test_the_sample_file_exists(personal_space: domain.SpaceKey) -> None:
    """Test that the test file exists."""
    file = manage_documents.get_file(TEST_FILE_NAME, personal_space)
    assert os.path.isfile(file), "The test file should exist."
    assert file.endswith(TEST_FILE_NAME), "The test file should have the correct name."


def test_chat_private_feature(features: domain.FeatureKey, saved_model_settings: ModelUsageSettingsCollection) -> None:
    """Run a query against the private chat feature."""
    prompt = """
    You are an AI designed to help humans with their daily activities.
    You are currently in a test enviroment to gauge whether this functionality works as expected.
    For this test, all you need to do is to echo back the input and append from docq at the end of it.

    Below is a sample expected input (SampleInput) and output (SampleOutput).
    SampleInput: Hello World
    SampleOutput: Hello World from docq

    Now, let's get started with the following input.
    INPUT: {input}
    """
    thread_id = 0

    # Run the query
    results = run_queries.query(
        prompt.format(input="Test 1"),
        features[config.FeatureType.CHAT_PRIVATE.name],
        thread_id,
        model_settings_collection=saved_model_settings,
    )
    assert "Test 1 from docq" in results[1][1], "The query should return the expected response."


def test_ask_personal_docs_feature(
    features: domain.FeatureKey,
    personal_space: domain.SpaceKey,
    saved_model_settings: ModelUsageSettingsCollection
    ) -> None:
    """Run a query against the personal ask feature."""
    prompt = """
    What is the official docq website?
    """
    thread_id = 0

    # Run the query
    results = run_queries.query(
        prompt,
        features[config.FeatureType.ASK_PERSONAL.name],
        thread_id,
        model_settings_collection=saved_model_settings,
        space=personal_space,
    )
    ai_response: str = results[1][1]
    assert "https://docq.ai" in ai_response, "The query should return the expected response."
