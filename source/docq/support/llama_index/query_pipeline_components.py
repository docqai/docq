"""Custom Llama Index query pipeline components."""

from typing import Any, Dict, List, Optional, Self

from llama_index.core.bridge.pydantic import Field
from llama_index.core.llms import LLM, ChatMessage, MessageRole
from llama_index.core.query_pipeline import CustomQueryComponent
from llama_index.core.schema import MetadataMode, NodeWithScore

DEFAULT_CONTEXT_PROMPT = (
    "Here is some context that may be relevant:\n"
    "-----\n"
    "{context_str}\n"
    "-----\n"
    "Please write a response to the following question, using the above context:\n"
    "{query_str}\n"
)


class ResponseWithChatHistory(CustomQueryComponent):
    """Response with chat history.

    Args:
      system_prompt: Optional[str] - System prompt to use for the LLM
      context_prompt: str - Context prompt to use for the LLM
      Inputs: dict
          chat_history: List[ChatMessage] - Chat history. Forms the message collection sent to the LLM for response generation. The context user message is appended to the end of this.
          nodes: List[NodeWithScore] - Context nodes from retrieval. Optionally, after being reranked. Each nodes text is added to the context user prompt for final response generation.
          query_str: str - the user query. Used added to the context user prompt for final response generation.
      Output: dict
          response: str - The generated response from the LLM
          source_nodes: List[NodeWithScore] - The source nodes used to generate the response.
    """

    llm: LLM = Field(..., description="LLM")
    system_prompt: Optional[str] = Field(default=None, description="System prompt to use for the LLM")
    context_prompt: str = Field(
        default=DEFAULT_CONTEXT_PROMPT,
        description="Context prompt to use for the LLM",
    )
    # query_str: Optional[str] = Field(default=None, description="The user query")

    # chat_history: Optional[List[ChatMessage]] = Field(default=None, description="Chat history")

    # nodes: Optional[List[NodeWithScore]] = Field(
    #     default=None, description="Context nodes from retrieval after being reranked."
    # )

    def _validate_component_inputs(self: Self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        # NOTE: this is OPTIONAL but we show you where to do validation as an example
        return input

    @property
    def _input_keys(self: Self) -> set:
        """Input keys dict."""
        # NOTE: These are required inputs. If you have optional inputs please override
        # `optional_input_keys_dict`
        return {"chat_history", "nodes", "query_str"}

    @property
    def _output_keys(self: Self) -> set:
        return {"response", "source_nodes"}

    def _prepare_context(
        self: Self,
        chat_history: List[ChatMessage],
        nodes: List[NodeWithScore],
        query_str: str,
    ) -> List[ChatMessage]:
        node_context = ""
        for idx, node in enumerate(nodes):
            node_text = node.get_content(metadata_mode=MetadataMode.LLM)
            node_context += f"Context Chunk {idx}:\n{node_text}\n\n"

        formatted_context = self.context_prompt.format(context_str=node_context, query_str=query_str)
        user_message = ChatMessage(role=MessageRole.USER, content=formatted_context)

        chat_history.append(user_message)

        if self.system_prompt is not None:
            chat_history = [ChatMessage(role=MessageRole.SYSTEM, content=self.system_prompt)] + chat_history

        return chat_history

    def _run_component(self: Self, **kwargs: Any) -> Dict[str, Any]:
        """Run the component."""
        chat_history = kwargs["chat_history"]
        nodes = kwargs["nodes"]
        query_str = kwargs["query_str"]

        prepared_context = self._prepare_context(chat_history, nodes, query_str)

        response = self.llm.chat(prepared_context)
        return {"response": response, "source_nodes": nodes}

    async def _arun_component(self: Self, **kwargs: Any) -> Dict[str, Any]:
        """Run the component asynchronously."""
        # NOTE: Optional, but async LLM calls are easy to implement
        chat_history = kwargs["chat_history"]
        nodes = kwargs["nodes"]
        query_str = kwargs["query_str"]

        prepared_context = self._prepare_context(chat_history, nodes, query_str)

        response = await self.llm.achat(prepared_context)

        return {"response": response, "source_nodes": nodes}
