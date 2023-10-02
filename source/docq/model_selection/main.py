"""Model selection for Docq."""

import logging as log
from dataclasses import dataclass
from enum import Enum
from typing import List

from ..config import SystemSettingsKey
from ..manage_settings import get_organisation_settings, update_organisation_settings
from typing import Dict


class ModelVendor(str, Enum):
    """This usually maps to a hosting provider + service name such as AzureML, Azure OpenAI, OpenAI, AWS SageMaker, or AWS Bedrock."""

    OPENAI = "OpenAI"
    AZURE_OPENAI = "Azure OpenAI"
    AZUREML = "AzureML"
    AWS_BEDROCK = "AWS Bedrock"
    AWS_SAGEMAKER = "AWS Sagemaker"


class ModelCapability(str, Enum):
    """Model capability."""

    CHAT = "Chat"
    EMBEDDING = "Embedding"
    TRANSLATION = "Translation"
    QUESTION_ANSWER = "Question Answer"
    SUMMARISATION = "Summarisation"
    IMAGE = "Image"
    AUDIO = "Audio"


@dataclass
class ModelUsageSettings:
    """Model usage settings."""

    model_vendor: ModelVendor

    model_name: str
    """This value is defined in the infrastructure. LLM hosting services such as AzureML Online Endpoints and AWS SageMaker Endpoints require a deployment name be given to each instance of a model deployed behind an endpoint. This is used to route traffic to the correct model."""
    model_capability: ModelCapability
    temperature: float = 0.0
    """Each LLM hosting provider defines string name to identify different version of models."""
    model_deployment_name: str = None


@dataclass
class ModelUsageSettingsCollection:
    """Model usage settings collection."""

    name: str
    """Friendly name of the model collection."""
    key: str
    """Unique key for the model collection."""
    model_usage_settings: Dict[ModelCapability, ModelUsageSettings]


# LLM_MODELS = {
#     "OPENAI_CHAT": (["gpt-3.5-turbo", "gpt-4"], range(0, 2)),
#     "OPENAI": (["text-davinci-003", "text-davinci-002", "code-davinci-002"], range(0, 2)),
#     "AZURE_OPENAI_CHAT": (["gpt-3.5-turbo", "gpt-4"], range(0, 2)),
#     "AZURE_OPENAI": (["text-davinci-003", "text-davinci-002", "code-davinci-002"], range(0, 2)),
# }


# We potentially need to support multiple versions and configurations for models form a given vendor
# The top level key uniquely identifies a model configuration
# At the second level key is the model capability
LLM_MODEL_COLLECTIONS2 = {
    "openai_latest": {
        "name": "OpenAI Latest",
        ModelCapability.CHAT: ModelUsageSettings(
            model_vendor=ModelVendor.OPENAI, model_name="gpt-3.5-turbo", model_capability=ModelCapability.CHAT
        ),
        ModelCapability.EMBEDDING: ModelUsageSettings(
            model_vendor=ModelVendor.OPENAI,
            model_name="text-embedding-ada-002",
            model_capability=ModelCapability.EMBEDDING,
        ),
    },
    "azure_openai_latest": {
        "name": "Azure OpenAI Latest",
        ModelCapability.CHAT: ModelUsageSettings(
            model_vendor=ModelVendor.AZURE_OPENAI,
            model_name="gpt-35-turbo",
            model_deployment_name="gpt-35-turbo",
            model_capability=ModelCapability.CHAT,
        ),
        ModelCapability.EMBEDDING: ModelUsageSettings(
            model_vendor=ModelVendor.AZURE_OPENAI,
            model_name="text-embedding-ada-002",
            model_deployment_name="text-embedding-ada-002",
            model_capability=ModelCapability.EMBEDDING,
        ),
    },
}

LLM_MODEL_COLLECTIONS = {
    "openai_latest": ModelUsageSettingsCollection(
        name="OpenAI Latest",
        key="openai_latest",
        model_usage_settings={
            ModelCapability.CHAT: ModelUsageSettings(
                model_vendor=ModelVendor.OPENAI, model_name="gpt-3.5-turbo", model_capability=ModelCapability.CHAT
            ),
            ModelCapability.EMBEDDING: ModelUsageSettings(
                model_vendor=ModelVendor.OPENAI,
                model_name="text-embedding-ada-002",
                model_capability=ModelCapability.EMBEDDING,
            ),
        },
    ),
    "azure_openai_latest": ModelUsageSettingsCollection(
        name="Azure OpenAI Latest",
        key="azure_openai_latest",
        model_usage_settings={
            ModelCapability.CHAT: ModelUsageSettings(
                model_vendor=ModelVendor.AZURE_OPENAI,
                model_name="gpt-35-turbo",
                model_deployment_name="gpt-35-turbo",
                model_capability=ModelCapability.CHAT,
            ),
            ModelCapability.EMBEDDING: ModelUsageSettings(
                model_vendor=ModelVendor.AZURE_OPENAI,
                model_name="text-embedding-ada-002",
                model_deployment_name="text-embedding-ada-002",
                model_capability=ModelCapability.EMBEDDING,
            ),
        },
    ),
}


# eventually model setting need to be associated with each feature that's interacts with the model


def get_model_settings_collection(model_settings_collection_key: str) -> ModelUsageSettingsCollection:
    """Get the settings for the model."""
    try:
        return LLM_MODEL_COLLECTIONS[model_settings_collection_key]
    except KeyError as e:
        log.error(
            "No model settings collection found for key:'%s'",
            model_settings_collection_key,
        )
        raise KeyError(f"No model settings collection found for key:'{model_settings_collection_key}'") from e


def get_saved_model_settings_collection(org_id: int) -> ModelUsageSettingsCollection:
    """Get the settings for the saved model."""
    saved_setting = get_organisation_settings(org_id, SystemSettingsKey.MODEL_COLLECTION)

    if saved_setting is None:
        log.error("No saved model settings collection found for organisation: '%s'", org_id)
        raise KeyError(f"No saved setting for key 'MODEL_COLLECTION' found for organisation: {org_id}")

    return get_model_settings_collection(saved_setting)


def list_available_model_settings_collections() -> dict:
    """List available models."""
    return {k: v.name for k, v in LLM_MODEL_COLLECTIONS.items()}
