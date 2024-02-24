"""Functions for utilising LLMs."""

import logging as log
import os
from typing import Any, Dict

import docq
from llama_index import (
    Response,
    ServiceContext,
    StorageContext,
    SummaryIndex,
    load_index_from_storage,
)
from llama_index.callbacks.base import CallbackManager
from llama_index.chat_engine import SimpleChatEngine
from llama_index.chat_engine.types import AGENT_CHAT_RESPONSE_TYPE, AgentChatResponse
from llama_index.embeddings import AzureOpenAIEmbedding, OpenAIEmbedding, OptimumEmbedding
from llama_index.embeddings.base import BaseEmbedding
from llama_index.indices.base import BaseIndex
from llama_index.indices.composability import ComposableGraph
from llama_index.llms.base import LLM, ChatMessage, MessageRole
from llama_index.llms.litellm import LiteLLM
from llama_index.node_parser import NodeParser, SentenceSplitter
from llama_index.prompts.base import ChatPromptTemplate
from llama_index.response.schema import RESPONSE_TYPE
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from ..config import EXPERIMENTS
from ..domain import SpaceKey
from ..manage_assistants import Persona, llama_index_chat_prompt_template_from_persona
from ..model_selection.main import (
    LLM_MODEL_COLLECTIONS,
    LlmUsageSettingsCollection,
    ModelCapability,
    ModelVendor,
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

TEXT_QA_SYSTEM_PROMPT = ChatMessage(
    content=(
        "You are an expert Q&A system that is trusted around the world."
        "Always answer the query using the provided context information and chat message history, "
        "and not prior knowledge."
        "Some rules to follow:"
        "1. Never directly reference the given context in your answer."
        "2. Avoid statements like 'Based on the context, ...' or "
        "'The context information ...' or '... given context information.' or anything along "
        "those lines."
    ),
    role=MessageRole.SYSTEM,
)


TEXT_QA_PROMPT_TMPL_MSGS = [
    TEXT_QA_SYSTEM_PROMPT,
    ChatMessage(
        content=(
            "Chat message history is below:"
            "---------------------"
            "{history_str}"
            "---------------------"
            "Context information is below:"
            "---------------------"
            "{context_str}"
            "---------------------"
            "Given the context information and chat message history but not prior knowledge from your training, "
            "answer the query below in British English."
            "Query: {query_str}"
            "Answer: "
        ),
        role=MessageRole.USER,
    ),
]

CHAT_TEXT_QA_PROMPT = ChatPromptTemplate(message_templates=TEXT_QA_PROMPT_TMPL_MSGS)


# def _get_model() -> OpenAI:
#     return OpenAI(temperature=0, model_name="text-davinci-003")


@tracer.start_as_current_span(name="_init_local_models")
def _init_local_models() -> None:
    """Initialize local models."""
    for model_collection in LLM_MODEL_COLLECTIONS.values():
        for model_usage_settings in model_collection.model_usage_settings.values():
            if model_usage_settings.service_instance_config.vendor == ModelVendor.HUGGINGFACE_OPTIMUM_BAAI:
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
        if chat_model_settings.service_instance_config.vendor == ModelVendor.AZURE_OPENAI:
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
        elif chat_model_settings.service_instance_config.vendor == ModelVendor.OPENAI:
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
        elif chat_model_settings.service_instance_config.vendor == ModelVendor.GOOGLE_VERTEXAI_PALM2:
            # GCP project_id is coming from the credentials json.
            model = LiteLLM(
                temperature=chat_model_settings.temperature,
                model=sc.model_name,
                callback_manager=_callback_manager,
            )
        elif chat_model_settings.service_instance_config.vendor == ModelVendor.GOOGLE_VERTEXTAI_GEMINI_PRO:
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
        elif chat_model_settings.service_instance_config.vendor == ModelVendor.GROQ_META:
            model = LiteLLM(
                temperature=chat_model_settings.temperature,
                model=f"openai/{sc.model_name}",
                api_key=sc.api_key,
                api_base=sc.api_base,
                max_tokens=4096,
                callback_manager=_callback_manager,
                kwargs={
                    "set_verbose": True,
                },
            )
            _env_missing = not bool(sc.api_key)
            if _env_missing:
                log.warning("Chat model: env var values missing.")
        else:
            raise ValueError("Chat model: model settings with a supported model vendor not found.")

        model.max_retries = 3

        print("model: ", model)
        print("model_settings_collection: ", model_settings_collection)

        return model


@tracer.start_as_current_span(name="_get_embed_model")
def _get_embed_model(model_settings_collection: LlmUsageSettingsCollection) -> BaseEmbedding | None:
    embedding_model = None
    if model_settings_collection and model_settings_collection.model_usage_settings[ModelCapability.EMBEDDING]:
        embedding_model_settings = model_settings_collection.model_usage_settings[ModelCapability.EMBEDDING]
        _callback_manager = CallbackManager([OtelCallbackHandler(tracer_provider=trace.get_tracer_provider())])
        with tracer.start_as_current_span(
            name=f"LangchainEmbedding.{embedding_model_settings.service_instance_config.vendor}"
        ):
            if embedding_model_settings.service_instance_config.vendor == ModelVendor.AZURE_OPENAI:
                embedding_model = AzureOpenAIEmbedding(
                    model=embedding_model_settings.service_instance_config.model_name,
                    azure_deployment=embedding_model_settings.service_instance_config.model_deployment_name,  # `deployment_name` is an alias
                    azure_endpoint=os.getenv("DOCQ_AZURE_OPENAI_API_BASE"),
                    api_key=os.getenv("DOCQ_AZURE_OPENAI_API_KEY1"),
                    # openai_api_type="azure",
                    api_version=os.getenv("DOCQ_AZURE_OPENAI_API_VERSION"),
                    callback_manager=_callback_manager,
                )
            elif embedding_model_settings.service_instance_config.vendor == ModelVendor.OPENAI:
                embedding_model = OpenAIEmbedding(
                    model=embedding_model_settings.service_instance_config.model_name,
                    api_key=os.getenv("DOCQ_OPENAI_API_KEY"),
                    callback_manager=_callback_manager,
                )
            elif embedding_model_settings.service_instance_config.vendor == ModelVendor.HUGGINGFACE_OPTIMUM_BAAI:
                embedding_model = OptimumEmbedding(
                    folder_name=get_models_dir(embedding_model_settings.service_instance_config.model_name),
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


@tracer.start_as_current_span(name="run_chat")
def run_chat(
    input_: str, history: str, model_settings_collection: LlmUsageSettingsCollection, persona: Persona
) -> AgentChatResponse:
    """Chat directly with a LLM with history."""
    ## chat engine handles tracking the history.
    print("persona: ", persona.system_prompt_content)
    engine = SimpleChatEngine.from_defaults(
        service_context=_get_service_context(model_settings_collection),
        kwargs=model_settings_collection.model_usage_settings[ModelCapability.CHAT].additional_args,
        system_prompt=persona.system_prompt_content
    )
    output = engine.chat(input_)

    log.debug("(Chat) Q: %s, A: %s", input_, output)
    return output


@tracer.start_as_current_span(name="run_ask")
def run_ask(
    input_: str,
    history: str,
    model_settings_collection: LlmUsageSettingsCollection,
    persona: Persona,
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
        summaries = []
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
                s_text = s_.summary if s_.summary else ""
                # s_text = index_.as_query_engine().query("What is a summary of this document?", )
                summaries.append(s_text)
                span.add_event(name="summary_appended", attributes={"index_summary": s_text})
            except Exception as e:
                span.set_status(status=Status(StatusCode.ERROR))
                span.record_exception(e)
                log.warning(
                    "Index for space '%s' failed to load, skipping. Maybe the index isn't created yet. Error message: %s",
                    s_,
                    e,
                )
                continue

        log.debug("number summaries: %s", len(summaries))
        span.set_attribute("number_summaries", len(summaries))
        with tracer.start_as_current_span(name="ComposableGraph.from_indices") as span:
            try:
                graph = ComposableGraph.from_indices(
                    SummaryIndex,
                    indices,
                    index_summaries=summaries,
                    service_context=_get_service_context(model_settings_collection),
                    kwargs=model_settings_collection.model_usage_settings[ModelCapability.CHAT].additional_args,
                )

                custom_query_engines = {
                    index.index_id: index.as_query_engine(child_branch_factor=2) for index in indices
                }

                query_engine = graph.as_query_engine(
                    custom_query_engines=custom_query_engines,
                    text_qa_template=llama_index_chat_prompt_template_from_persona(persona).partial_format(history_str=history),
                )

                prompts_dict = query_engine.get_prompts()
                print("prompts:", list(prompts_dict.keys()))

                output = query_engine.query(input_)
                span.add_event(
                    name="ask_combined_spaces",
                    attributes={"question": input_, "answer": str(output), "spaces_count": len(spaces)},
                )
                log.debug("(Ask combined spaces %s) Q: %s, A: %s", spaces, input_, output)
            except Exception as e:
                span.set_status(status=Status(StatusCode.ERROR))
                span.record_exception(e)
                log.error(
                    "run_ask(): Failed to create ComposableGraph. Maybe there was an issue with one of the Space indexes. Error message: %s",
                    e,
                )
                span.set_status(status=Status(StatusCode.ERROR))
                span.record_exception(e)
    else:
        span.set_attribute("spaces_count", 0)
        log.debug("runs_ask(): space None or zero. Assuming personal ASK.")
        # No additional spaces i.e. likely to be against a user's documents in their personal space.

        log.debug("runs_ask(): space is None. executing run_chat(), not ASK.")
        output = run_chat(
            input_=input_, history=history, model_settings_collection=model_settings_collection, persona=persona
        )
        span.add_event(name="ask_without_spaces", attributes={"question": input_, "answer": str(output)})
        # index = _load_index_from_storage(space=space, model_settings_collection=model_settings_collection)
        # engine = index.as_chat_engine(
        #     verbose=True,
        #     similarity_top_k=3,
        #     vector_store_query_mode="default",
        #     chat_mode=ChatMode.CONDENSE_QUESTION,
        # )
        # output = engine.chat(input_)
        # log.debug("(Ask %s w/o shared spaces) Q: %s, A: %s", space, input_, output)

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
