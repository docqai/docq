"""Model selection for Docq."""

from dataclasses import dataclass


@dataclass
class ModelUsageSettings:
    """Model usage settings."""

    model_vendor: str
    model_name: str
    temperature: float = 0.0


LLM_MODELS = {
    "OPENAI_CHAT": (["gpt-3.5-turbo", "gpt-4"], range(0, 2)),
    "OPENAI": (["text-davinci-003", "text-davinci-002", "code-davinci-002"], range(0, 2)),
    "AZURE_OPENAI_CHAT": (["gpt-3.5-turbo", "gpt-4"], range(0, 2)),
    "AZURE_OPENAI": (["text-davinci-003", "text-davinci-002", "code-davinci-002"], range(0, 2)),
}
