"""Docq backend integration tests."""

import os
from contextlib import suppress
from shutil import rmtree
from typing import Generator

import pytest
from docq import config, domain, manage_documents, manage_settings, manage_users, run_queries, setup
from docq.model_selection.main import (
    LlmUsageSettingsCollection,
    get_saved_model_settings_collection,
)

from tests.utilities import (
    AI_MODEL_COLLECTION_NAME,
    DOCQ_DATA_KEY,
    TEST_FILE_NAME,
    get_auth_results,
    get_features,
    get_sample_file,
    get_user,
)
from web.utils.constants import SessionKeyNameForAuth


@pytest.fixture(scope="session" , autouse=True)
def _setup_and_teardown() -> Generator[None, None, None]:
    """Setup and teardown for each test."""
    print("Setup")
    # setup_env()
    setup.init()

    yield
    print("Teardown")
    with suppress(FileNotFoundError):
        rmtree(os.environ[DOCQ_DATA_KEY])


@pytest.fixture(scope="session")
def test_user() -> dict:
    """Get a test user."""
    return get_user()

## User actions

# Create user
@pytest.fixture(scope="session")
def user_id(test_user: dict) -> int:
    """Create a test user."""
    return manage_users.create_user(**test_user)


# Login
@pytest.fixture(scope="session")
def auth_results(test_user: dict, user_id: int) -> dict:
    """Authenticate the test user."""
    return get_auth_results(test_user, user_id)


@pytest.fixture(scope="session")
def features(auth_results: dict) -> dict[str, domain.FeatureKey]:
    """Get available features."""
    return get_features(auth_results[SessionKeyNameForAuth.ID.name])


@pytest.fixture(scope="session")
def shared_space(auth_results: dict) -> domain.SpaceKey:
    """Get personal space."""
    return domain.SpaceKey(
        domain.SpaceType.SHARED,
        auth_results[SessionKeyNameForAuth.ID.name],
        auth_results[SessionKeyNameForAuth.SELECTED_ORG_ID.name]
    )


@pytest.fixture(scope="session")
def sample_file() -> bytes:
    """Get test file."""
    return get_sample_file()


# Upload file to a personal space
@pytest.fixture(autouse=True, scope="session")
def _upload_test_file(sample_file: bytes, shared_space: domain.SpaceKey) -> None:
    """Upload a test file."""
    manage_documents.upload(TEST_FILE_NAME, sample_file, shared_space)


# Update organisation settings
@pytest.fixture(autouse=True, scope="session")
def _update_organisation_settings(auth_results: dict) -> None:
    """Update organisation settings."""
    manage_settings.update_organisation_settings(
        {
            config.OrganisationSettingsKey.ENABLED_FEATURES.name: [
                f.name for f in config.OrganisationFeatureType
            ],
            config.OrganisationSettingsKey.MODEL_COLLECTION.name: AI_MODEL_COLLECTION_NAME,
        },
        org_id=auth_results[SessionKeyNameForAuth.SELECTED_ORG_ID.name],
    )


# Get saved model settings
@pytest.fixture(scope="session")
def saved_model_settings(auth_results: dict) -> LlmUsageSettingsCollection:
    """Get saved model settings."""
    return get_saved_model_settings_collection(
        auth_results[SessionKeyNameForAuth.SELECTED_ORG_ID.name]
    )


# Run tests
def test_user_exists(test_user: dict) -> None:
    """Test that user exists."""
    assert manage_users.authenticate(**test_user) is not None, "The test user should exist."


def test_the_sample_file_exists(shared_space: domain.SpaceKey) -> None:
    """Test that the test file exists."""
    file = manage_documents.get_file(TEST_FILE_NAME, shared_space)
    assert os.path.isfile(file), "The test file should exist."
    assert file.endswith(TEST_FILE_NAME), "The test file should have the correct name."


def test_chat_private_feature(features: dict[str, domain.FeatureKey], saved_model_settings: LlmUsageSettingsCollection) -> None:
    """Run a query against the private chat feature i.e. directly with the LLM no RAG.

    This also tests that query() correctly selects which completion function to run based on spaces existing or not.
    """
    system_prompt = """
    You are an AI designed to help humans with their daily activities.
    You are currently in a test environment to gauge whether this functionality works as expected.
    For this test, all you need to do is to echo back the input and append from docq at the end of it.

    Below is a sample expected input (SampleInput) and output (SampleOutput).
    SampleInput: Hello World
    SampleOutput: Hello World from docq
    """

    user_prompt_template_content = """
        Now, let's get started with the following input.\n
        INPUT: {input}
    """

    persona = domain.Persona(
        key="test-persona",
        name="Test Persona",
        system_prompt_content=system_prompt,
        user_prompt_template_content=user_prompt_template_content,)

    thread_id = 0

    # Run the query
    results = run_queries.query(
        "Test 1",
        features[config.OrganisationFeatureType.CHAT_PRIVATE.name],
        thread_id,
        model_settings_collection=saved_model_settings,
        persona=persona,
    )
    assert "Test 1 from docq" in results[1][1], f"The query didn't return the expected response. Returned: '{results[1][1]}', expected: 'Test 1 from docq'"
