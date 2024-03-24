"""Model selection and usage settings for Docq.

We potentially need to support multiple versions and configurations for models from a given vendor and also different combinations of models.
The ModeUsageSettings class is the building block.
We might have multiple structures to group multiple models together.
Model collections grouped by vendor and model capability is just one way to structure.
"""

import logging as log
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Mapping, Optional

from vertexai.preview.generative_models import HarmBlockThreshold, HarmCategory

from ..config import ENV_VAR_DOCQ_GROQ_API_KEY, OrganisationSettingsKey
from ..manage_settings import get_organisation_settings


class ModelVendor(str, Enum):
    """Model vendor names.

    Dedicated model providers {model vendor} e.g. OPENAI OR COHERE.
    Cloud provider hosted models {cloud provider name}_[{service name}_]{model vendor} e.g. AZURE_OPENAI OR AWS_SAGEMAKER_LLAMA OR AWS_BEDROCK_COHERE or AWS_BEDROCK_TITAN.
    """

    OPENAI = "OpenAI"
    AZURE_OPENAI = "Azure OpenAI"
    AZURE_ML_LLAMA = "Azure ML Llama"
    GROQ_META = "Groq Meta"
    AWS_BEDROCK_AMAZON = "AWS Bedrock Amazon"
    AWS_BEDROCK_AI21LABs = "AWS Bedrock AI21labs"
    AWS_BEDROCK_COHERE = "AWS Bedrock Cohere"
    AWS_BEDROCK_ANTHROPIC = "AWS Bedrock Anthropic"
    AWS_BEDROCK_STABILITYAI = "AWS Bedrock StabilityAI"
    AWS_SAGEMAKER_META = "AWS Sagemaker Meta"
    HUGGINGFACE_OPTIMUM_BAAI = "HuggingFace Optimum BAAI"
    GOOGLE_VERTEXAI_PALM2 = "Google VertexAI Palm2"
    GOOGLE_VERTEXTAI_GEMINI_PRO = "Google VertexAI Gemini Pro"


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
    TEXT = "Text"
    VISION = "Vision"


@dataclass
class LlmServiceInstanceConfig:
    """Config related to a running instance of an LLM aka a deployed model."""

    vendor: ModelVendor
    model_name: str
    """Each LLM hosting provider defines string name to identify different versions of models."""
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    """Service endpoint base URL."""
    api_type: Optional[str] = None
    """OpenAI and Azure OpenAI use this."""
    api_version: Optional[str] = None
    """Cloud provider API version. Applies to Azure."""
    model_deployment_name: Optional[str] = None
    """This value is defined in the infrastructure. LLM hosting services such as AzureML Online Endpoints and AWS SageMaker Endpoints require a deployment name be given to each instance of a model deployed behind an endpoint. This is used to route traffic to the correct model."""
    citation: Optional[str] = None
    """Any citation information for the model. Typically applies to open source models."""
    context_window_size: Optional[int] = None
    """The maximum context size to be sent to the LLM. This can't be larger than the maximum context size supported by the LLM."""
    license_: Optional[str] = None
    """The licenses under which the model is released. Especially important for open source models."""
    additional_properties: Dict[str, Any] = field(default_factory=dict)
    """Any additional properties that are specific to the model hosting service."""


@dataclass
class LlmUsageSettings:
    """Model usage settings to associate with a model service instance."""

    model_capability: ModelCapability
    """Map a capability to a model intance."""
    service_instance_config: LlmServiceInstanceConfig
    """Config for a running instance of an LLM compatible with these settings."""
    temperature: float = 0.0
    additional_args: Optional[Mapping[str, Any]] = field(default_factory=dict)
    """Any additional model API specific arguments to be passed to function like chat and completion"""


@dataclass
class LlmUsageSettingsCollection:
    """Model usage settings collection."""

    name: str
    """Friendly name of the model collection."""
    key: str
    """Unique key for the model collection."""
    model_usage_settings: Dict[ModelCapability, LlmUsageSettings]

# The configuration of the deployed instances of models. Basically service discovery.
LLM_SERVICE_INSTANCES = {
    "openai-gpt35turbo": LlmServiceInstanceConfig(
        vendor=ModelVendor.OPENAI,
        model_name="gpt-3.5-turbo",
        api_key=os.getenv("DOCQ_OPENAI_API_KEY"),
        license_="Commercial",
    ),
    "openai-ada-002": LlmServiceInstanceConfig(
        vendor=ModelVendor.OPENAI,
        model_name="text-embedding-ada-002",
        api_key=os.getenv("DOCQ_OPENAI_API_KEY"),
        license_="Commercial",
    ),
    "azure-openai-gpt35turbo": LlmServiceInstanceConfig(
        vendor=ModelVendor.AZURE_OPENAI,
        model_name="gpt-35-turbo",
        model_deployment_name="gpt-35-turbo",
        api_base=os.getenv("DOCQ_AZURE_OPENAI_API_BASE") or "",
        api_key=os.getenv("DOCQ_AZURE_OPENAI_API_KEY1") or "",
        api_version=os.environ.get("DOCQ_AZURE_OPENAI_API_VERSION", "2023-05-15"),
        context_window_size=4096,
        license_="Commercial",
    ),
    "azure-openai-gpt4turbo": LlmServiceInstanceConfig(
        vendor=ModelVendor.AZURE_OPENAI,
        model_name="gpt-4",
        model_deployment_name="gpt4-turbo-1106-preview",
        api_base=os.getenv("DOCQ_AZURE_OPENAI_API_BASE") or "",
        api_key=os.getenv("DOCQ_AZURE_OPENAI_API_KEY1") or "",
        api_version=os.environ.get("DOCQ_AZURE_OPENAI_API_VERSION", "2023-05-15"),
        license_="Commercial",
    ),
    "azure-openai-ada-002": LlmServiceInstanceConfig(
        vendor=ModelVendor.AZURE_OPENAI,
        model_name="text-embedding-ada-002",
        model_deployment_name="text-embedding-ada-002",
        api_base=os.getenv("DOCQ_AZURE_OPENAI_API_BASE") or "",
        api_key=os.getenv("DOCQ_AZURE_OPENAI_API_KEY1") or "",
        license_="Commercial",
    ),
    "google-vertexai-palm2": LlmServiceInstanceConfig(
        vendor=ModelVendor.GOOGLE_VERTEXAI_PALM2, model_name="chat-bison@002", context_window_size=8196
    ),
    "google-vertexai-gemini-pro": LlmServiceInstanceConfig(
        vendor=ModelVendor.GOOGLE_VERTEXTAI_GEMINI_PRO,
        model_name="gemini-pro",
        additional_properties={"vertex_location": "us-central1"},
        context_window_size=32000,
    ),
    "google-vertexai-gemini-1.0-pro-001": LlmServiceInstanceConfig(
        vendor=ModelVendor.GOOGLE_VERTEXTAI_GEMINI_PRO,
        model_name="gemini-1.0-pro-001",
        additional_properties={"vertex_location": "us-central1"},
        context_window_size=32000,
    ),
    "optimum-bge-small-en-v1.5": LlmServiceInstanceConfig(
        vendor=ModelVendor.HUGGINGFACE_OPTIMUM_BAAI,
        model_name="BAAI/bge-small-en-v1.5",
        license_="MIT",
        citation="""@misc{bge_embedding,
                            title={C-Pack: Packaged Resources To Advance General Chinese Embedding},
                            author={Shitao Xiao and Zheng Liu and Peitian Zhang and Niklas Muennighoff},
                            year={2023},
                            eprint={2309.07597},
                            archivePrefix={arXiv},
                            primaryClass={cs.CL}
                            }""",
        context_window_size=1024,
    ),
    "groq-meta-llama2-70b-4096": LlmServiceInstanceConfig(
        vendor=ModelVendor.GROQ_META,
        model_name="llama2-70b-4096",
        api_key=os.getenv(ENV_VAR_DOCQ_GROQ_API_KEY),
        api_base="https://api.groq.com/openai/v1",
        api_version="2023-05-15",  # not used by groq but checked by the downstream lib
        context_window_size=4096,
    ),
    "groq-meta-mixtral-8x7b-32768": LlmServiceInstanceConfig(
        vendor=ModelVendor.GROQ_META,
        model_name="mixtral-8x7b-32768",
        api_key=os.getenv(ENV_VAR_DOCQ_GROQ_API_KEY),
        api_base="https://api.groq.com/openai/v1",
        api_version="2023-05-15",  # not used by groq but checked by the downstream lib
        context_window_size=32768,
    ),
}


# NOTE: we are using LiteLLM client via Llama Index as the LLM client interface. This means model names need to follow the LiteLLM naming convention.
# SoT https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json
LLM_MODEL_COLLECTIONS = {
    "openai_latest": LlmUsageSettingsCollection(
        name="OpenAI Latest",
        key="openai_latest",
        model_usage_settings={
            ModelCapability.CHAT: LlmUsageSettings(
                model_capability=ModelCapability.CHAT,
                temperature=0.7,
                service_instance_config=LLM_SERVICE_INSTANCES["openai-gpt35turbo"],
            ),
            ModelCapability.EMBEDDING: LlmUsageSettings(
                model_capability=ModelCapability.EMBEDDING,
                service_instance_config=LLM_SERVICE_INSTANCES["openai-ada-002"],
            ),
        },
    ),
    "azure_openai_latest": LlmUsageSettingsCollection(
        name="Azure OpenAI Latest",
        key="azure_openai_latest",
        model_usage_settings={
            ModelCapability.CHAT: LlmUsageSettings(
                model_capability=ModelCapability.CHAT,
                temperature=0.7,
                service_instance_config=LLM_SERVICE_INSTANCES["azure-openai-gpt35turbo"],
            ),
            ModelCapability.EMBEDDING: LlmUsageSettings(
                model_capability=ModelCapability.EMBEDDING,
                service_instance_config=LLM_SERVICE_INSTANCES["azure-openai-ada-002"],
            ),
        },
    ),
    "azure_openai_with_local_embedding": LlmUsageSettingsCollection(
        name="Azure OpenAI wth Local Embedding",
        key="azure_openai_with_local_embedding",
        model_usage_settings={
            ModelCapability.CHAT: LlmUsageSettings(
                model_capability=ModelCapability.CHAT,
                temperature=0.7,
                service_instance_config=LLM_SERVICE_INSTANCES["azure-openai-gpt35turbo"],
            ),
            ModelCapability.EMBEDDING: LlmUsageSettings(
                model_capability=ModelCapability.EMBEDDING,
                service_instance_config=LLM_SERVICE_INSTANCES["optimum-bge-small-en-v1.5"],
            ),
        },
    ),
    "azure_openai_gpt4turbo_with_local_embedding": LlmUsageSettingsCollection(
        name="Azure OpenAI GPT4 Turbo wth Local Embedding",
        key="azure_openai_gpt4turbo_with_local_embedding",
        model_usage_settings={
            ModelCapability.CHAT: LlmUsageSettings(
                model_capability=ModelCapability.CHAT,
                temperature=0.7,
                service_instance_config=LLM_SERVICE_INSTANCES["azure-openai-gpt4turbo"],
            ),
            ModelCapability.EMBEDDING: LlmUsageSettings(
                model_capability=ModelCapability.EMBEDDING,
                service_instance_config=LLM_SERVICE_INSTANCES["optimum-bge-small-en-v1.5"],
            ),
        },
    ),
    "groq_llma2_70b_with_local_embedding": LlmUsageSettingsCollection(
        name="Groq Llama2 70B wth Local Embedding",
        key="groq_llama2_70b_with_local_embedding",
        model_usage_settings={
            ModelCapability.CHAT: LlmUsageSettings(
                model_capability=ModelCapability.CHAT,
                temperature=0.7,
                service_instance_config=LLM_SERVICE_INSTANCES["groq-meta-llama2-70b-4096"],
            ),
            ModelCapability.EMBEDDING: LlmUsageSettings(
                model_capability=ModelCapability.EMBEDDING,
                service_instance_config=LLM_SERVICE_INSTANCES["optimum-bge-small-en-v1.5"],
            ),
        },
    ),
    "groq_mixtral_8x7b_with_local_embedding": LlmUsageSettingsCollection(
        name="Groq Mixtral 8x7b wth Local Embedding",
        key="groq_mixtral_8x7b_with_local_embedding",
        model_usage_settings={
            ModelCapability.CHAT: LlmUsageSettings(
                model_capability=ModelCapability.CHAT,
                temperature=0.7,
                service_instance_config=LLM_SERVICE_INSTANCES["groq-meta-mixtral-8x7b-32768"],
            ),
            ModelCapability.EMBEDDING: LlmUsageSettings(
                model_capability=ModelCapability.EMBEDDING,
                service_instance_config=LLM_SERVICE_INSTANCES["optimum-bge-small-en-v1.5"],
            ),
        },
    ),
    "google_vertexai_palm2_latest": LlmUsageSettingsCollection(
        name="Google VertexAI Palm2 Latest",
        key="google_vertexai_palm2_latest",
        model_usage_settings={
            ModelCapability.CHAT: LlmUsageSettings(
                model_capability=ModelCapability.CHAT,
                temperature=0.7,
                service_instance_config=LLM_SERVICE_INSTANCES["google-vertexai-palm2"],
            ),
            ModelCapability.EMBEDDING: LlmUsageSettings(
                model_capability=ModelCapability.EMBEDDING,
                service_instance_config=LLM_SERVICE_INSTANCES["optimum-bge-small-en-v1.5"],
            ),
        },
    ),
    "google_vertexai_gemini_pro_latest": LlmUsageSettingsCollection(
        name="Google VertexAI Gemini Pro Latest",
        key="google_vertexai_gemini_pro_latest",
        model_usage_settings={
            ModelCapability.CHAT: LlmUsageSettings(
                model_capability=ModelCapability.CHAT,
                service_instance_config=LLM_SERVICE_INSTANCES["google-vertexai-gemini-pro"],
                temperature=0.7,
                additional_args={
                    "safety_settings": {
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    },
                },
            ),
            ModelCapability.EMBEDDING: LlmUsageSettings(
                model_capability=ModelCapability.EMBEDDING,
                service_instance_config=LLM_SERVICE_INSTANCES["optimum-bge-small-en-v1.5"],
            ),
        },
    ),
}


# eventually model setting need to be associated with each feature that's interacts with the model


def get_model_settings_collection(model_settings_collection_key: str) -> LlmUsageSettingsCollection:
    """Get the settings for the model."""
    try:
        return LLM_MODEL_COLLECTIONS[model_settings_collection_key]
    except KeyError as e:
        log.error(
            "No model settings collection found for key:'%s'",
            model_settings_collection_key,
        )
        raise KeyError(f"No model settings collection found for key:'{model_settings_collection_key}'") from e


def get_saved_model_settings_collection(org_id: int) -> LlmUsageSettingsCollection:
    """Get the settings for the saved model."""
    saved_setting = get_organisation_settings(org_id, OrganisationSettingsKey.MODEL_COLLECTION)

    if saved_setting is None:
        log.error("No saved model settings collection found for organisation: '%s'", org_id)
        raise KeyError(f"No saved setting for key 'MODEL_COLLECTION' found for organisation: {org_id}")

    return get_model_settings_collection(saved_setting)  # type: ignore


def list_available_model_settings_collections() -> dict:
    """List available models."""
    return {k: v.name for k, v in LLM_MODEL_COLLECTIONS.items()}
