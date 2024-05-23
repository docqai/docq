"""Functions for utilising LLMs."""

import logging as log
import os
from typing import Any, Dict, List
from uu import Error

import docq
from llama_index.core.base.llms.types import ChatMessage
from llama_index.core.base.response.schema import RESPONSE_TYPE, Response
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.chat_engine.types import AGENT_CHAT_RESPONSE_TYPE, AgentChatResponse
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.indices.base import BaseIndex
from llama_index.core.indices.loading import load_index_from_storage
from llama_index.core.llms import LLM
from llama_index.core.node_parser import NodeParser, SentenceSplitter
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import BaseRetriever, QueryFusionRetriever
from llama_index.core.retrievers.fusion_retriever import FUSION_MODES
from llama_index.core.service_context import ServiceContext

# load_index_from_storage
from llama_index.core.storage import StorageContext
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.embeddings.huggingface_optimum import OptimumEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.litellm import LiteLLM
from llama_index.retrievers.bm25 import BM25Retriever
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from ..config import EXPERIMENTS
from ..domain import SpaceKey
from ..manage_assistants import Assistant, llama_index_chat_prompt_template_from_assistant
from ..model_selection.main import (
    LLM_MODEL_COLLECTIONS,
    LlmUsageSettingsCollection,
    ModelCapability,
    ModelProvider,
)
from .llamaindex_otel_callbackhandler import OtelCallbackHandler

# from .metadata_extractors import DocqEntityExtractor, DocqMetadataExtractor
# from .node_parsers import AsyncSimpleNodeParser
from .store import get_index_dir, get_models_dir

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


@tracer.start_as_current_span(name="_get_generation_model")
def _get_generation_model(model_settings_collection: LlmUsageSettingsCollection) -> LLM | None:
    import litellm

    litellm.telemetry = False
    model = None
    if model_settings_collection and model_settings_collection.model_usage_settings[ModelCapability.CHAT]:
        chat_model_settings = model_settings_collection.model_usage_settings[ModelCapability.CHAT]
        sc = chat_model_settings.service_instance_config
        _callback_manager = CallbackManager([OtelCallbackHandler(tracer_provider=trace.get_tracer_provider())])
        if sc.provider == ModelProvider.AZURE_OPENAI:
            _additional_kwargs: Dict[str, Any] = {}
            _additional_kwargs["api_version"] = chat_model_settings.service_instance_config.api_version
            model = LiteLLM(
                temperature=chat_model_settings.temperature,
                model=f"azure/{sc.model_deployment_name}",
                additional_kwargs=_additional_kwargs,
                api_base=sc.api_base,
                api_key=sc.api_key,
                set_verbose=True,
                callback_manager=_callback_manager,
            )
            log.info("Chat model: using Azure OpenAI")
            _env_missing = not bool(sc.api_base and sc.api_key and sc.api_version)
            if _env_missing:
                log.warning("Chat model: env var values missing.")
        elif sc.provider == ModelProvider.OPENAI:
            model = LiteLLM(
                temperature=chat_model_settings.temperature,
                model=sc.model_name,
                api_key=sc.api_key,
                callback_manager=_callback_manager,
            )
            log.info("Chat model: using OpenAI.")
            _env_missing = not bool(sc.api_key)
            if _env_missing:
                log.warning("Chat model: env var values missing")
        elif sc.provider == ModelProvider.GOOGLE_VERTEXAI_PALM2:
            # GCP project_id is coming from the credentials json.
            model = LiteLLM(
                temperature=chat_model_settings.temperature,
                model=sc.model_name,
                callback_manager=_callback_manager,
            )
        elif sc.provider == ModelProvider.GOOGLE_VERTEXTAI_GEMINI_PRO:
            # GCP project_id is coming from the credentials json.
            model = LiteLLM(
                temperature=chat_model_settings.temperature,
                model=sc.model_name,
                callback_manager=_callback_manager,
                max_tokens=2048,
                kwargs={"telemetry": False},
            )
            litellm.VertexAIConfig()
            litellm.vertex_location = sc.additional_properties["vertex_location"]
        elif sc.provider == ModelProvider.GROQ:
            model = LiteLLM(
                temperature=chat_model_settings.temperature,
                model=f"groq/{sc.model_name}",
                api_key=sc.api_key,
                # api_base=sc.api_base,
                # max_tokens=4096,
                callback_manager=_callback_manager,
                kwargs={
                    "set_verbose": True,
                },
            )
            _env_missing = not bool(sc.api_key)
            if _env_missing:
                log.warning("Chat model: env var values missing.")
        else:
            raise ValueError("Chat model: model settings with a supported model provider not found.")

        model.max_retries = 3

        log.info("model: ", model)
        log.info("model_settings_collection: ", model_settings_collection)

        return model


@tracer.start_as_current_span(name="_get_embed_model")
def _get_embed_model(model_settings_collection: LlmUsageSettingsCollection) -> BaseEmbedding | None:
    embedding_model = None
    if model_settings_collection and model_settings_collection.model_usage_settings[ModelCapability.EMBEDDING]:
        embedding_model_settings = model_settings_collection.model_usage_settings[ModelCapability.EMBEDDING]
        _callback_manager = CallbackManager([OtelCallbackHandler(tracer_provider=trace.get_tracer_provider())])
        sc = embedding_model_settings.service_instance_config
        with tracer.start_as_current_span(name=f"LangchainEmbedding.{sc.provider}"):
            if sc.provider == ModelProvider.AZURE_OPENAI:
                embedding_model = AzureOpenAIEmbedding(
                    model=sc.model_name,
                    azure_deployment=sc.model_deployment_name,  # `deployment_name` is an alias
                    azure_endpoint=os.getenv("DOCQ_AZURE_OPENAI_API_BASE"),
                    api_key=os.getenv("DOCQ_AZURE_OPENAI_API_KEY1"),
                    # openai_api_type="azure",
                    api_version=os.getenv("DOCQ_AZURE_OPENAI_API_VERSION"),
                    callback_manager=_callback_manager,
                )
            elif sc.provider == ModelProvider.OPENAI:
                embedding_model = OpenAIEmbedding(
                    model=sc.model_name,
                    api_key=os.getenv("DOCQ_OPENAI_API_KEY"),
                    callback_manager=_callback_manager,
                )
            elif sc.provider == ModelProvider.HUGGINGFACE_OPTIMUM_BAAI:
                embedding_model = OptimumEmbedding(
                    folder_name=get_models_dir(sc.model_name),
                    callback_manager=_callback_manager,
                )
            else:
                # defaults
                embedding_model = OpenAIEmbedding()

    return embedding_model


@tracer.start_as_current_span(name="_get_default_storage_context")
def _get_default_storage_context() -> StorageContext:
    return StorageContext.from_defaults()


@tracer.start_as_current_span(name="_get_storage_context")
def _get_storage_context(space: SpaceKey) -> StorageContext:
    return StorageContext.from_defaults(persist_dir=get_index_dir(space))


@tracer.start_as_current_span(name="_get_service_context")
def _get_service_context(model_settings_collection: LlmUsageSettingsCollection) -> ServiceContext:
    log.debug(
        "EXPERIMENTS['INCLUDE_EXTRACTED_METADATA']['enabled']: %s", EXPERIMENTS["INCLUDE_EXTRACTED_METADATA"]["enabled"]
    )
    log.debug("EXPERIMENTS['ASYNC_NODE_PARSER']['enabled']: %s", EXPERIMENTS["ASYNC_NODE_PARSER"]["enabled"])

    _node_parser = None  # use default node parser
    if EXPERIMENTS["INCLUDE_EXTRACTED_METADATA"]["enabled"]:
        _node_parser = _get_node_parser(model_settings_collection)
        if EXPERIMENTS["ASYNC_NODE_PARSER"]["enabled"]:
            log.debug("loading async node parser.")
            # _node_parser = _get_async_node_parser(model_settings_collection)
    else:
        _callback_manager = CallbackManager([OtelCallbackHandler(tracer_provider=trace.get_tracer_provider())])
        _node_parser = SentenceSplitter.from_defaults(callback_manager=_callback_manager)

    return ServiceContext.from_defaults(
        llm=_get_generation_model(model_settings_collection),
        node_parser=_node_parser,
        embed_model=_get_embed_model(model_settings_collection),
        callback_manager=_node_parser.callback_manager,
        context_window=model_settings_collection.model_usage_settings[
            ModelCapability.CHAT
        ].service_instance_config.context_window_size,
        num_output=256,  # default in lama-index but we need to be explicit here because it's not being set everywhere.
    )


@tracer.start_as_current_span(name="_get_node_parser")
def _get_node_parser(model_settings_collection: LlmUsageSettingsCollection) -> NodeParser:
    # metadata_extractor = MetadataExtractor(
    #     extractors=[

    #         KeywordExtractor(llm=_get_generation_model(model_settings_collection), keywords=5),
    #         EntityExtractor(label_entities=True, device="cpu"),
    #         # CustomExtractor()
    #     ],
    # )
    _callback_manager = CallbackManager([OtelCallbackHandler(tracer_provider=trace.get_tracer_provider())])
    node_parser = SentenceSplitter.from_defaults()

    return node_parser


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


@tracer.start_as_current_span(name="_load_index_from_storage")
def _load_index_from_storage(space: SpaceKey, model_settings_collection: LlmUsageSettingsCollection) -> BaseIndex:
    # set service context explicitly for multi model compatibility
    sc = _get_service_context(model_settings_collection)
    return load_index_from_storage(
        storage_context=_get_storage_context(space), service_context=sc, callback_manager=sc.callback_manager
    )


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


@tracer.start_as_current_span(name="run_ask")
def run_ask(
    input_: str,
    history: List[ChatMessage],
    model_settings_collection: LlmUsageSettingsCollection,
    assistant: Assistant,
    spaces: list[SpaceKey] | None = None,
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
