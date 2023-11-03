"""Model selection and usage settings for Docq.

We potentially need to support multiple versions and configurations for models from a given vendor and also different combinations of models.
The ModeUsageSettings class is the building block.
We might have multiple structures to group multiple models together.
Model collections grouped by vendor and model capability is just one way to structure.
"""

import logging as log
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional

from ..config import SystemSettingsKey
from ..manage_settings import get_organisation_settings


class ModelVendor(str, Enum):
    """Model vendor names.

    Dedicated model providers {model vendor} e.g. OPENAI OR COHERE.
    Cloud provider hosted models {cloud provider name}_[{service name}_]{model vendor} e.g. AZURE_OPENAI OR AWS_SAGEMAKER_LLAMA OR AWS_BEDROCK_COHERE or AWS_BEDROCK_TITAN.
    """

    OPENAI = "OpenAI"
    AZURE_OPENAI = "Azure OpenAI"
    AZURE_ML_LLAMA = "Azure ML Llama"
    AWS_BEDROCK_AMAZON = "AWS Bedrock Amazon"
    AWS_BEDROCK_AI21LABs = "AWS Bedrock AI21labs"
    AWS_BEDROCK_COHERE = "AWS Bedrock Cohere"
    AWS_BEDROCK_ANTHROPIC = "AWS Bedrock Anthropic"
    AWS_BEDROCK_STABILITYAI = "AWS Bedrock StabilityAI"
    AWS_SAGEMAKER_META = "AWS Sagemaker Meta"
    HUGGINGFACE_OPTIMUM_BAAI = "HuggingFace Optimum BAAI"


class ModelCapability(str, Enum):
    """Model capability."""

    CHAT = "Chat"
    EMBEDDING = "Embedding"
    INSTRUCTION = "Instruction"
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
    model_deployment_name: Optional[str] = None
    """Each LLM hosting provider defines string name to identify different version of models."""
    citation: Optional[str] = None
    """Any citation information for the model. Typically applies to open source models."""
    license_: Optional[str] = None
    """The licenses under which the model is released. Especially important for open source models."""

@dataclass
class ModelUsageSettingsCollection:
    """Model usage settings collection."""

    name: str
    """Friendly name of the model collection."""
    key: str
    """Unique key for the model collection."""
    model_usage_settings: Dict[ModelCapability, ModelUsageSettings]


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
    "azure_openai_with_local_embedding": ModelUsageSettingsCollection(
        name="Azure OpenAI wth Local Embedding",
        key="azure_openai_with_local_embedding",
        model_usage_settings={
            ModelCapability.CHAT: ModelUsageSettings(
                model_vendor=ModelVendor.AZURE_OPENAI,
                model_name="gpt-35-turbo",
                model_deployment_name="gpt-35-turbo",
                model_capability=ModelCapability.CHAT,
            ),
            ModelCapability.EMBEDDING: ModelUsageSettings(
                model_vendor=ModelVendor.HUGGINGFACE_OPTIMUM_BAAI,
                model_name="BAAI/bge-small-en-v1.5",
                model_capability=ModelCapability.EMBEDDING,
                license_="MIT",
                citation="""@misc{bge_embedding,
                            title={C-Pack: Packaged Resources To Advance General Chinese Embedding}, 
                            author={Shitao Xiao and Zheng Liu and Peitian Zhang and Niklas Muennighoff},
                            year={2023},
                            eprint={2309.07597},
                            archivePrefix={arXiv},
                            primaryClass={cs.CL}
                            }""",
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
