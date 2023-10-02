"""Model selection for Docq."""

import logging as log
from dataclasses import dataclass
from enum import Enum
from typing import List

from ..config import SystemSettingsKey
from ..manage_settings import get_organisation_settings, update_organisation_settings
from typing import Dict


class ModelVendor(str, Enum):
    """Model vendors."""

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

    model_vendor: str
    """This usually maps to a hosting provider service name such as AzureML, Azure OpenAI, OpenAI, AWS SageMaker, or AWS Bedrock."""
    model_name: str
    """This value is defined in the infrastructure. LLM hosting services such as AzureML Online Endpoints and AWS SageMaker Endpoints require a deployment name be given to each instance of a model deployed behind an endpoint. This is used to route traffic to the correct model."""
    model_capability: ModelCapability
    temperature: float = 0.0
    """Each LLM hosting provider defines string name to identify different version of models."""
    model_deployment_name: str = None


# LLM_MODELS = {
#     "OPENAI_CHAT": (["gpt-3.5-turbo", "gpt-4"], range(0, 2)),
#     "OPENAI": (["text-davinci-003", "text-davinci-002", "code-davinci-002"], range(0, 2)),
#     "AZURE_OPENAI_CHAT": (["gpt-3.5-turbo", "gpt-4"], range(0, 2)),
#     "AZURE_OPENAI": (["text-davinci-003", "text-davinci-002", "code-davinci-002"], range(0, 2)),
# }


# We potentially need to support multiple versions and configurations for models form a given vendor
# The top level key uniquely identifies a model configuration
# At the second level key is the model capability
LLM_MODEL_COLLECTIONS = {
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


# TODO: replace with DB persistance and session state at the UI layer
# eventually model setting need to be associated with each feature that's interacts with the model


def get_saved_model_settings_collection(org_id: int) -> dict:
    """Get the settings for the saved model."""
    saved_setting = get_organisation_settings(org_id, SystemSettingsKey.MODEL_COLLECTION)

    return LLM_MODEL_COLLECTIONS[saved_setting] if saved_setting else LLM_MODEL_COLLECTIONS[ModelVendor.AZURE_OPENAI]


def list_available_models() -> dict:
    """List available models."""
    return {k: v["name"] for k, v in LLM_MODEL_COLLECTIONS.items()}
