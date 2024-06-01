"""Functions for utilising LLMs."""

import logging as log
import os
from typing import Any, Dict, List, Optional
from uu import Error

import docq
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.base.response.schema import RESPONSE_TYPE, Response
from llama_index.core.bridge.pydantic import Field
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.chat_engine.types import AGENT_CHAT_RESPONSE_TYPE, AgentChatResponse
from llama_index.core.indices.base import BaseIndex
from llama_index.core.llms import LLM, ChatMessage, MessageRole
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.query_pipeline import CustomQueryComponent
from llama_index.core.retrievers import BaseRetriever, QueryFusionRetriever
from llama_index.core.retrievers.fusion_retriever import FUSION_MODES
from llama_index.core.schema import MetadataMode, NodeWithScore

# load_index_from_storage
from llama_index.embeddings.huggingface_optimum import OptimumEmbedding
from llama_index.retrievers.bm25 import BM25Retriever
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from ..domain import SpaceKey
from ..manage_assistants import Assistant, llama_index_chat_prompt_template_from_persona
from ..manage_indices import _load_index_from_storage, load_indices_from_storage
from ..model_selection.main import (
    LLM_MODEL_COLLECTIONS,
    LlmUsageSettingsCollection,
    ModelCapability,
    ModelProvider,
    _get_service_context,
)

# from .metadata_extractors import DocqEntityExtractor, DocqMetadataExtractor
# from .node_parsers import AsyncSimpleNodeParser
from .store import get_models_dir

tracer = trace.get_tracer(__name__, docq.__version_str__)


ERROR_PROMPT = """
Examine the following error and provide a simple response for the user
Example: if the error is token limit based, simply say "Sorry, your question is too long, please try again with a shorter question"
if you can't understand the error, simply say "Sorry I cannot offer any assistance on the error message"
Make sure your response is in the first person context
ERROR: {error}
"""


@tracer.start_as_current_span(name="_init_local_models")
def _init_local_models() -> None:
    """Initialize local models."""
    for model_collection in LLM_MODEL_COLLECTIONS.values():
        for model_usage_settings in model_collection.model_usage_settings.values():
            if model_usage_settings.service_instance_config.provider == ModelProvider.HUGGINGFACE_OPTIMUM_BAAI:
                model_dir = get_models_dir(model_usage_settings.service_instance_config.model_name, makedir=False)
                if not os.path.exists(model_dir):
                    model_dir = get_models_dir(model_usage_settings.service_instance_config.model_name, makedir=True)
                    OptimumEmbedding.create_and_save_optimum_model(
                        model_usage_settings.service_instance_config.model_name,
                        model_dir,
                    )


DEFAULT_CONTEXT_PROMPT = (
    "Here is some context that may be relevant:\n"
    "-----\n"
    "{context_str}\n"
    "-----\n"
    "Please write a response to the following question, using the above context:\n"
    "{query_str}\n"
)


class ResponseWithChatHistory(CustomQueryComponent):
    """Response with chat history."""

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

    def _validate_component_inputs(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Validate component inputs during run_component."""
        # NOTE: this is OPTIONAL but we show you where to do validation as an example
        return input

    @property
    def _input_keys(self) -> set:
        """Input keys dict."""
        # NOTE: These are required inputs. If you have optional inputs please override
        # `optional_input_keys_dict`
        return {"chat_history", "nodes", "query_str"}

    @property
    def _output_keys(self) -> set:
        return {"response"}

    def _prepare_context(
        self,
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

    def _run_component(self, **kwargs) -> Dict[str, Any]:
        """Run the component."""
        chat_history = kwargs["chat_history"]
        nodes = kwargs["nodes"]
        query_str = kwargs["query_str"]

        prepared_context = self._prepare_context(chat_history, nodes, query_str)

        response = self.llm.chat(prepared_context)

        return {"response": response}

    async def _arun_component(self, **kwargs: Any) -> Dict[str, Any]:
        """Run the component asynchronously."""
        # NOTE: Optional, but async LLM calls are easy to implement
        chat_history = kwargs["chat_history"]
        nodes = kwargs["nodes"]
        query_str = kwargs["query_str"]

        prepared_context = self._prepare_context(chat_history, nodes, query_str)

        response = await self.llm.achat(prepared_context)

        return {"response": response}


# @tracer.start_as_current_span(name="_get_async_node_parser")
# def _get_async_node_parser(model_settings_collection: ModelUsageSettingsCollection) -> AsyncSimpleNodeParser:

#     metadata_extractor = DocqMetadataExtractor(
#         extractors=[
#             #KeywordExtractor(llm=_get_chat_model_using_langchain(model_settings_collection), keywords=5),
#         ],
#         async_extractors=[
#             DocqEntityExtractor(label_entities=True, device="cpu"),
#         ]
#     )
#     #TODO: if async node parser
#     node_parser = AsyncSimpleNodeParser.from_defaults(  # SimpleNodeParser is the default when calling ServiceContext.from_defaults()

#     )

#     return node_parser




def get_hybrid_fusion_retriever_query(
    indices: List[BaseIndex], model_settings_collection: LlmUsageSettingsCollection, similarity_top_k: int = 4
) -> BaseRetriever:
    """Hybrid fusion retriever query."""
    retrievers = []
    for index in indices:
        vector_retriever = index.as_retriever(similarity_top_k=similarity_top_k)
        retrievers.append(vector_retriever)
        bm25_retriever = BM25Retriever.from_defaults(docstore=index.docstore, similarity_top_k=similarity_top_k)
        retrievers.append(bm25_retriever)

    # the default prompt doesn't return JUST the list of queries when using some none OAI models like Llama3.
    QUERY_GEN_PROMPT = (
        "You are a helpful assistant that generates multiple search queries based on a "
        "single input <query>. You only generate the queries and NO other text. "
        "Strictly DO NOT change the name of things that appear in the <query> like the name of people, companies, and products. e.g don't change 'docq' to 'docquity'"
        "Generate {num_queries} search queries, one on each line, "
        "related to the following input query:\n"
        "<query>{query}<query>\n"
        "Queries:\n"
    )
    # Create a FusionRetriever to merge and rerank the results
    fusion_retriever = QueryFusionRetriever(
        retrievers,
        similarity_top_k=4,
        num_queries=4,  # set this to 1 to disable query generation
        mode=FUSION_MODES.RECIPROCAL_RANK,
        use_async=False,
        verbose=True,
        llm=_get_service_context(model_settings_collection).llm,
        callback_manager=_get_service_context(model_settings_collection).callback_manager,
        query_gen_prompt=QUERY_GEN_PROMPT,  # we could override the query generation prompt here
    )
    return fusion_retriever


@tracer.start_as_current_span(name="run_chat")
def run_chat(
    input_: str, history: List[ChatMessage], model_settings_collection: LlmUsageSettingsCollection, assistant: Assistant
) -> AgentChatResponse:
    """Chat directly with a LLM with history."""
    ## chat engine handles tracking the history.
    log.debug("chat assistant: ", assistant.system_message_content)

    engine = SimpleChatEngine.from_defaults(
        service_context=_get_service_context(model_settings_collection),
        kwargs=model_settings_collection.model_usage_settings[ModelCapability.CHAT].additional_args,
        system_prompt=assistant.system_message_content,
        chat_history=history,
    )
    output = engine.chat(input_)

    # log.debug("(Chat) Q: %s, A: %s", input_, output)
    return output


def run_ask(
    input_: str,
    history: List[ChatMessage],
    model_settings_collection: LlmUsageSettingsCollection,
    assistant: Assistant,
    spaces: list[SpaceKey] | None = None,
) -> RESPONSE_TYPE | AGENT_CHAT_RESPONSE_TYPE:
    return run_ask2(input_, history, model_settings_collection, persona, spaces)


@tracer.start_as_current_span(name="run_ask")
def run_ask1(
    input_: str,
    history: List[ChatMessage],
    model_settings_collection: LlmUsageSettingsCollection,
    persona: Assistant,
    spaces: Optional[list[SpaceKey]] = None,
) -> RESPONSE_TYPE | AGENT_CHAT_RESPONSE_TYPE:
    """Ask questions against existing index(es) with history."""
    log.debug("exec: runs_ask()")
    span = trace.get_current_span()

    if spaces is not None and len(spaces) > 0:
        span.set_attribute("spaces_count", len(spaces))
        log.debug("runs_ask(): spaces count: %s", len(spaces))
        # With additional spaces likely to be combining a number of shared spaces.
        indices = []
        # summaries = []
        output = _default_response()
        for s_ in spaces:
            try:
                index_ = _load_index_from_storage(s_, model_settings_collection)

                log.debug("run_chat(): %s, %s", index_.index_id, s_.summary)
                indices.append(index_)
                span.add_event(
                    name="index_appended",
                    attributes={"index_id": index_.index_id, "index_struct_cls": index_.index_struct_cls.__name__},
                )
                # s_text = s_.summary if s_.summary else ""
                # # s_text = index_.as_query_engine().query("What is a summary of this document?", )
                # summaries.append(s_text)
                # span.add_event(name="summary_appended", attributes={"index_summary": s_text})
            except Exception as e:
                span.set_status(status=Status(StatusCode.ERROR))
                span.record_exception(e)
                log.warning(
                    "Index for space '%s' failed to load, skipping. Maybe the index isn't created yet. Error message: %s",
                    s_,
                    e,
                )
                continue

        try:
            text_qa_template = llama_index_chat_prompt_template_from_assistant(assistant, history)
            span.add_event(name="prompt_created")
        except Exception as e:
            raise Error(f"Error: {e}") from e

        try:
            retriever = get_hybrid_fusion_retriever_query(indices, model_settings_collection)
            span.add_event(name="retriever_object_created", attributes={"retriever": retriever.__class__.__name__})

            query_engine = RetrieverQueryEngine.from_args(
                retriever,
                service_context=_get_service_context(model_settings_collection),
                text_qa_template=text_qa_template,
            )
            span.add_event(name="query_engine__object_created")

            output = query_engine.query(input_)
            span.add_event(name="query_executed")
        except Exception as e:
            span.set_status(status=Status(StatusCode.ERROR))
            span.record_exception(e)
            raise Error(f"Error: {e}") from e

    else:
        span.set_attribute("spaces_count", 0)
        log.debug("runs_ask(): space None or zero.")
        # No additional spaces i.e. likely to be against a user's documents in their personal space.

        output = Response("You need to select a Space or upload a document to ask a questions.")
        span.add_event(name="ask_without_spaces", attributes={"question": input_, "answer": str(output)})

    return output


@tracer.start_as_current_span(name="run_ask2")
def run_ask2(
    input_: str,
    history: List[ChatMessage],
    model_settings_collection: LlmUsageSettingsCollection,
    persona: Assistant,
    spaces: Optional[list[SpaceKey]] = None,
) -> RESPONSE_TYPE | AGENT_CHAT_RESPONSE_TYPE:
    """Implements logic of run_ask() using LlamaIndex query pipelines."""
    span = trace.get_current_span()

    try:
        indices = []
        if spaces is not None and len(spaces) > 0:
            indices = load_indices_from_storage(spaces, model_settings_collection)
        text_qa_template = llama_index_chat_prompt_template_from_persona(persona, history)
        span.add_event(name="prompt_created")
        retriever = indices[0].as_retriever(similarity_top_k=6)
        # retriever = get_hybrid_fusion_retriever_query(indices, model_settings_collection)
        span.add_event(name="retriever_object_created", attributes={"retriever": retriever.__class__.__name__})

        # query_engine = RetrieverQueryEngine.from_args(
        #     retriever=retriever,
        #     service_context=_get_service_context(model_settings_collection),
        #     text_qa_template=text_qa_template,
        # )
        span.add_event(name="query_engine__object_created")

        # output = query_engine.query(input_)
        # span.add_event(name="query_executed")
    except Exception as e:
        span.set_status(status=Status(StatusCode.ERROR))
        span.record_exception(e)
        raise Error(f"Error: {e}") from e

    from llama_index.core.prompts import PromptTemplate
    from llama_index.core.query_pipeline import (
        ArgPackComponent,
        InputComponent,
        QueryPipeline,
    )
    from llama_index.postprocessor.colbert_rerank import ColbertRerank

    # First, we create an input component to capture the user query
    input_component = InputComponent()

    # Next, we use the LLM to rewrite a user query
    rewrite = (
        "Please write a query to a semantic search engine using the current conversation.\n"
        "\n"
        "\n"
        "{chat_history_str}"
        "\n"
        "\n"
        "Latest message: {query_str}\n"
        'Query:"""\n'
    )
    rewrite_template = PromptTemplate(rewrite)

    llm = _get_service_context(model_settings_collection).llm

    # we will retrieve two times, so we need to pack the retrieved nodes into a single list
    argpack_component = ArgPackComponent()

    # using that, we will retrieve...
    # retriever = index.as_retriever(similarity_top_k=6)

    # then postprocess/rerank with Colbert
    reranker = ColbertRerank(top_n=3)

    response_component = ResponseWithChatHistory(
        llm=llm,
        system_prompt=persona.system_prompt_content,
        # system_prompt=(
        #     "You are a Q&A system. You will be provided with the previous chat history, "
        #     "as well as possibly relevant context, to assist in answering a user message."
        # ),
    )

    # define query pipeline
    pipeline = QueryPipeline(
        modules={
            "input": input_component,
            "rewrite_template": rewrite_template,
            "llm": llm,
            "rewrite_retriever": retriever,
            "query_retriever": retriever,
            "join": argpack_component,
            "reranker": reranker,
            "response_component": response_component,
        },
        verbose=False,
    )

    # run both retrievers -- once with the hallucinated query, once with the real query
    pipeline.add_link("input", "rewrite_template", src_key="query_str", dest_key="query_str")
    pipeline.add_link(
        "input",
        "rewrite_template",
        src_key="chat_history_str",
        dest_key="chat_history_str",
    )
    pipeline.add_link("rewrite_template", "llm")
    pipeline.add_link("llm", "rewrite_retriever")
    pipeline.add_link("input", "query_retriever", src_key="query_str")

    # each input to the argpack component needs a dest key -- it can be anything
    # then, the argpack component will pack all the inputs into a single list
    pipeline.add_link("rewrite_retriever", "join", dest_key="rewrite_nodes")
    pipeline.add_link("query_retriever", "join", dest_key="query_nodes")

    # reranker needs the packed nodes and the query string
    pipeline.add_link("join", "reranker", dest_key="nodes")
    pipeline.add_link("input", "reranker", src_key="query_str", dest_key="query_str")

    # synthesizer needs the reranked nodes and query str
    pipeline.add_link("reranker", "response_component", dest_key="nodes")
    pipeline.add_link("input", "response_component", src_key="query_str", dest_key="query_str")
    pipeline.add_link(
        "input",
        "response_component",
        src_key="chat_history",
        dest_key="chat_history",
    )

    # output, intermediates = pipeline.run_with_intermediates(input_)
    history_str = "\n".join([str(x) for x in history])
    output, intermediates = pipeline.run_with_intermediates(
        query_str=input_,
        chat_history=history,
        chat_history_str=history_str,
    )
    print("intermediates: ", intermediates)
    print("ANSWER:", output.message)
    return Response(output.message)


@tracer.start_as_current_span(name="_default_response")
def _default_response() -> Response:
    """A default response incase of any failure."""
    return Response("I don't know.")


@tracer.start_as_current_span(name="query_error")
def query_error(error: Exception, model_settings_collection: LlmUsageSettingsCollection) -> Response:
    """Query for a response to an error message."""
    try:  # Try re-prompting with the AI
        log.exception("Error: %s", error)
        input_ = ERROR_PROMPT.format(error=error)
        return SimpleChatEngine.from_defaults(service_context=_get_service_context(model_settings_collection)).chat(
            input_
        )
    except Exception as error:
        log.exception("Error: %s", error)
        return _default_response()
