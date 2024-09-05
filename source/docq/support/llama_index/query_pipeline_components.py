"""Custom Llama Index query pipeline components."""

from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional, Self

from llama_index.core.base.query_pipeline.query import (
    ChainableMixin,
    InputKeys,
    OutputKeys,
    QueryComponent,
    validate_and_convert_stringable,
)
from llama_index.core.bridge.pydantic import Field
from llama_index.core.llms import LLM, ChatMessage, MessageRole
from llama_index.core.prompts import BasePromptTemplate
from llama_index.core.prompts.default_prompts import DEFAULT_HYDE_PROMPT
from llama_index.core.prompts.mixin import (
    PromptDictType,
    PromptMixin,
    PromptMixinType,
)
from llama_index.core.query_pipeline import CustomQueryComponent
from llama_index.core.schema import MetadataMode, NodeWithScore, QueryBundle, QueryType
from llama_index.core.service_context_elements.llm_predictor import (
    LLMPredictorType,
)
from llama_index.core.settings import Settings

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

class BaseQueryTransform(ChainableMixin, PromptMixin):
    """Base class for query transform.

    A query transform augments a raw query string with associated transformations
    to improve index querying.

    The query transformation is performed before the query is sent to the index.
    FIXME: see note in QueryTransformComponent below
    """

    def _get_prompt_modules(self: Self) -> PromptMixinType:
        """Get prompt modules."""
        # TODO: keep this for now since response synthesizers don't generally have sub-modules
        return {}

    @abstractmethod
    def _run(self: Self, query_bundle: QueryBundle, metadata: Dict) -> QueryBundle:
        """Run query transform."""

    def run(
        self: Self,
        query_bundle_or_str: QueryType,
        metadata: Optional[Dict] = None,
    ) -> QueryBundle:
        """Run query transform."""
        metadata = metadata or {}
        if isinstance(query_bundle_or_str, str):
            query_bundle = QueryBundle(
                query_str=query_bundle_or_str,
                custom_embedding_strs=[query_bundle_or_str],
            )
        else:
            query_bundle = query_bundle_or_str

        return self._run(query_bundle, metadata=metadata)

    def __call__(
        self: Self,
        query_bundle_or_str: QueryType,
        metadata: Optional[Dict] = None,
    ) -> QueryBundle:
        """Run query processor."""
        return self.run(query_bundle_or_str, metadata=metadata)

    def _as_query_component(self: Self, **kwargs: Any) -> QueryComponent:
        """As query component."""
        return QueryTransformComponent(query_transform=self)



class QueryTransformComponent(QueryComponent):
    """Query transform component.

    FIXME: temp to fix a bug in _run_component. Remove once fix is merged upstream.
    """

    query_transform: BaseQueryTransform = Field(..., description="Query transform.")

    class Config:
        arbitrary_types_allowed = True

    def set_callback_manager(self: Self, callback_manager: Any) -> None:
        """Set callback manager."""
        # TODO: not implemented yet

    def _validate_component_inputs(self: Self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        if "query_str" not in input:
            raise ValueError("Input must have key 'query_str'")
        input["query_str"] = validate_and_convert_stringable(input["query_str"])

        input["metadata"] = input.get("metadata", {})

        return input

    def _run_component(self: Self, **kwargs: Any) -> Any:
        """Run component."""
        output = self.query_transform.run(
            kwargs["query_str"],
            metadata=kwargs["metadata"],
        )
        return {"query_str": output.query_str}

    async def _arun_component(self: Self, **kwargs: Any) -> Any:
        """Run component."""
        # TODO: true async not implemented yet
        return self._run_component(**kwargs)

    @property
    def input_keys(self: Self) -> InputKeys:
        """Input keys."""
        return InputKeys.from_keys({"query_str"}, optional_keys={"metadata"})

    @property
    def output_keys(self: Self) -> OutputKeys:
        """Output keys."""
        return OutputKeys.from_keys({"query_str"})


class HyDEQueryTransform(BaseQueryTransform):
    """Hypothetical Document Embeddings (HyDE) query transform.

    It uses an LLM to generate hypothetical answer(s) to a given query,
    and use the resulting documents as embedding strings.

    As described in `[Precise Zero-Shot Dense Retrieval without Relevance Labels]
    (https://arxiv.org/abs/2212.10496)`

    Note: this has been customised from the original implementation in Llama Index
    """

    def __init__(
        self,
        llm: Optional[LLMPredictorType] = None,
        hyde_prompt: Optional[BasePromptTemplate] = None,
        include_original: bool = True,
        prompt_args: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize HyDEQueryTransform.

        Args:
            llm_predictor (Optional[LLM]): LLM for generating
                hypothetical documents
            hyde_prompt (Optional[BasePromptTemplate]): Custom prompt for HyDE. query_str in passed into the prompt for replacement by default. Use `{query_str}`.
            include_original (bool): Whether to include original query
                string as one of the embedding strings
            prompt_args (Optional[Dict[str, Any]]): Additional arguments to be replaced in the prompt. key should be the variable in the template.
        """
        super().__init__()

        self._llm = llm or Settings.llm
        self._hyde_prompt = hyde_prompt or DEFAULT_HYDE_PROMPT
        self._include_original = include_original
        self._promp_args = prompt_args or {}

    def _get_prompts(self: Self) -> PromptDictType:
        """Get prompts."""
        return {"hyde_prompt": self._hyde_prompt}

    def _update_prompts(self: Self, prompts: PromptDictType) -> None:
        """Update prompts."""
        if "hyde_prompt" in prompts:
            self._hyde_prompt = prompts["hyde_prompt"]

    def _run(self: Self, query_bundle: QueryBundle, metadata: Dict) -> QueryBundle:
        """Run query transform."""
        # TODO: support generating multiple hypothetical docs
        query_str = query_bundle.query_str
        hypothetical_doc = self._llm.predict(self._hyde_prompt, query_str=query_str, **self._promp_args)
        embedding_strs = [hypothetical_doc]
        if self._include_original:
            embedding_strs.extend(query_bundle.embedding_strs)
        return QueryBundle(
            query_str=query_str,
            custom_embedding_strs=embedding_strs,
        )

class KwargPackComponent(QueryComponent):
    """Kwarg pack component.

    Packs arbitrary number of kwargs into a dict.

    """

    convert_fn: Optional[Callable] = Field(default=None, description="Function to convert output.")

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        raise NotImplementedError

    def validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs."""
        return input

    def _validate_component_outputs(self, output: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component outputs."""
        # make sure output value is a list
        if not isinstance(output["output"], dict):
            raise ValueError(f"Output is not a dict.")
        return output

    def set_callback_manager(self, callback_manager: Any) -> None:
        """Set callback manager."""

    def _run_component(self, **kwargs: Any) -> Any:
        """Run component."""
        if self.convert_fn is not None:
            for k, v in kwargs.items():
                kwargs[k] = self.convert_fn(v)
        return {"output": kwargs}

    async def _arun_component(self, **kwargs: Any) -> Any:
        """Run component (async)."""
        return self._run_component(**kwargs)

    @property
    def input_keys(self) -> InputKeys:
        """Input keys."""
        # NOTE: this shouldn't be used
        return InputKeys.from_keys(set(), optional_keys=set())

    @property
    def output_keys(self) -> OutputKeys:
        """Output keys."""
        return OutputKeys.from_keys({"output"})