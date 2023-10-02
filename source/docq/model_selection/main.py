"""Model selection for Docq."""

import logging as log
from dataclasses import dataclass
from enum import Enum
from typing import List

from ..config import SystemSettingsKey
from ..manage_settings import get_organisation_settings, update_organisation_settings


class ModelVendors(str, Enum):
    """Model vendors."""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    AZUREML = "azureml"
    AWS_BEDROCK = "aws_bedrock"
    AWS_SAGEMAKER = "aws_sagemaker"


class ModelCapability(str, Enum):
    """Model capability."""

    CHAT = "chat"
    EMBEDDING = "embedding"
    TRANSLATION = "translation"
    QUESTION_ANSWERING = "question_answering"
    SUMMARIZATION = "summarization"
    IMAGE = "image"
    AUDIO = "audio"


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
LLM_MODELS = {
    "openai": {
        "CHAT": ModelUsageSettings(
            model_vendor=ModelVendors.OPENAI, model_name="gpt-3.5-turbo", model_capability=ModelCapability.CHAT
        ),
        "EMBED": ModelUsageSettings(
            model_vendor=ModelVendors.OPENAI,
            model_name="text-embedding-ada-002",
            model_capability=ModelCapability.EMBEDDING,
        ),
    },
    "azure_openai": {
        "CHAT": ModelUsageSettings(
            model_vendor=ModelVendors.AZURE_OPENAI,
            model_name="gpt-35-turbo",
            model_deployment_name="gpt-35-turbo",
            model_capability=ModelCapability.CHAT,
        ),
        "EMBED": ModelUsageSettings(
            model_vendor=ModelVendors.AZURE_OPENAI,
            model_name="text-embedding-ada-002",
            model_deployment_name="text-embedding-ada-002",
            model_capability=ModelCapability.EMBEDDING,
        ),
    },
}


# TODO: replace with DB persistance and session state at the UI layer
# eventually model setting need to be associated with each feature that's interacts with the model


def get_selected_model_settings(org_id: int) -> dict:
    """Get the settings for the saved model."""
    saved_setting = get_organisation_settings(org_id, SystemSettingsKey.MODEL_VENDOR)

    return LLM_MODELS[saved_setting] if saved_setting else LLM_MODELS[ModelVendors.AZURE_OPENAI]


def set_selected_model(org_id: int, model_vendor: ModelVendors) -> None:
    """Save the selected model."""
    update_organisation_settings(SystemSettingsKey.MODEL_VENDOR.name, model_vendor.value, org_id)

    log.debug("Selected Model: %s", model_vendor)


def list_available_models() -> List[str]:
    """List available models."""
    return list(LLM_MODELS.keys())
