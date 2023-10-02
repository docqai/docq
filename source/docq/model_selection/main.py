"""Model selection for Docq."""

import logging as log
from dataclasses import dataclass
from enum import Enum
from typing import Optional


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
    """Each LLM hosting provider defines string name to identify different version of models."""
    model_deployment_name: str
    """This value is defined in the infrastructure. LLM hosting services such as AzureML Online Endpoints and AWS SageMaker Endpoints require a deployment name be given to each instance of a model deployed behind an endpoint. This is used to route traffic to the correct model."""
    model_capability: ModelCapability
    api_key_env_var_name: str
    temperature: Optional[float] = 0.0
    endpoint_url_env_var_name: Optional[str] = None


# LLM_MODELS = {
#     "OPENAI_CHAT": (["gpt-3.5-turbo", "gpt-4"], range(0, 2)),
#     "OPENAI": (["text-davinci-003", "text-davinci-002", "code-davinci-002"], range(0, 2)),
#     "AZURE_OPENAI_CHAT": (["gpt-3.5-turbo", "gpt-4"], range(0, 2)),
#     "AZURE_OPENAI": (["text-davinci-003", "text-davinci-002", "code-davinci-002"], range(0, 2)),
# }


LLM_MODELS = {
    "openai": {
        "CHAT": ModelUsageSettings("openai", "gpt-3.5-turbo", None, ModelCapability.CHAT, "OPENAI_API_KEY"),
        "EMBED": ModelUsageSettings(
            "openai", "text-embedding-ada-002", None, ModelCapability.EMBEDDING, "OPENAI_API_KEY"
        ),
    },
    "azure_openai": {
        "CHAT": ModelUsageSettings(
            "azure-openai",
            "gpt-35-turbo",
            "gpt-35-turbo",
            ModelCapability.CHAT,
            "DOCQ_AZURE_OPENAI_API_KEY1",
            "DOCQ_AZURE_OPENAI_BASE",
        ),
        "EMBED": ModelUsageSettings(
            "azure-openai",
            "text-embedding-ada-002",
            "text-embedding-ada-002",
            ModelCapability.EMBEDDING,
            "DOCQ_AZURE_OPENAI_API_KEY1",
            "DOCQ_AZURE_OPENAI_BASE",
        ),
    },
}

global SELECTED_MODEL

SELECTED_MODEL = LLM_MODELS[ModelVendors.OPENAI]


def get_selected_model() -> dict:
    """Get the selected model."""
    return SELECTED_MODEL


def set_selected_model(model_vendor: ModelVendors) -> None:
    """Set the selected model."""
    # NOTE: this be replaced with DB persistance
    SELECTED_MODEL = LLM_MODELS[model_vendor]  # noqa: N806
    log.debug("SELECTED_MODEL: %s", SELECTED_MODEL)
