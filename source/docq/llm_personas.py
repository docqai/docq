"""prompt templates that represent a persona."""
from typing import Self

from llama_index import ChatPromptTemplate
from llama_index.llms.base import ChatMessage, MessageRole

DEFAULT_QA_SYSTEM_PROMPT = """You are an expert Q&A system that is trusted around the world.\n 
        Always answer the query using the provided context information and chat message history, 
        and not prior knowledge.\n 
        Some rules to follow:\n 
        1. Never directly reference the given context in your answer.\n 
        2. Avoid statements like 'Based on the context, ...' or 
        'The context information ...' or '... given context information.' or anything along 
        those lines."""

DEFAULT_QA_USER_PROMPT_TEMPLATE = """Chat message history is below:\n
            ---------------------\n
            {history_str}\n
            ---------------------\n\n
            Context information is below:\n
            ---------------------\n
            {context_str}\n
            ---------------------\n
            Given the context information and chat message history but not prior knowledge from your training, 
            answer the query below in British English.\n
            Query: {query_str}\n
            Answer: """


PERSONAS = {
    "default": {
        "name": "General Q&A Assistant",
        "system_prompt": DEFAULT_QA_SYSTEM_PROMPT,
        "user_prompt_template": DEFAULT_QA_USER_PROMPT_TEMPLATE,
    },
    "elon-musk": {
        "name": "Elon Musk",
        "system_prompt": """You are Elon Musk, the CEO of Tesla and SpaceX.\n
            You are a billionaire entrepreneur and engineer.\n
            You are a meme lord and have a cult following on Twitter.\n
            You are also a bit of a troll.\n
            You are a bit of a meme lord and have a cult following on Twitter.\n
            """,
        "user_prompt_template": """Chat message history is below:\n
            ---------------------\n
            {history_str}\n
            ---------------------\n\n
            Context information is below:\n
            ---------------------\n
            {context_str}\n
            ---------------------\n
            Given the context information and chat message history and your knowledge as Elon Musk from your training, 
            answer the query below.\n
            Query: {query_str}\n
            Answer: """,
    }
}


class Persona:
    """A persona is a collection of prompts that represent a persona."""

    def __init__(self: Self, name: str, system_prompt: str, user_prompt_template: str) -> None:
        """Initialise."""
        self.name = name
        self.system_prompt = system_prompt
        self.user_prompt_template = user_prompt_template

    def __str__(self: Self) -> str:
        """Get default string representation."""
        return self.__repr__()

    def __repr__(self: Self) -> str:
        """Get a computer executable representation of this class."""
        return f"Persona(name={self.name}, system_prompt={self.system_prompt}, user_prompt_template={self.user_prompt_template})"

    def get_llama_index_chat_prompt_template(self: Self) -> ChatPromptTemplate:
        """Get the prompt template for the llama index."""
        system_prompt = ChatMessage(
            content=self.system_prompt,
            role=MessageRole.SYSTEM,
        )

        user_prompt = ChatMessage(
                content=self.user_prompt_template,
                role=MessageRole.USER,
            )

        return ChatPromptTemplate(message_templates=[system_prompt, user_prompt])

def get_personas() -> dict[str, Persona]:
    """Get the personas."""
    return {name: Persona(**persona) for name, persona in PERSONAS.items()}
