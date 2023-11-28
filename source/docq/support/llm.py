"""Functions for utilising LLMs."""

import logging as log
import os

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
from llama_index.chat_engine.types import AGENT_CHAT_RESPONSE_TYPE, AgentChatResponse, ChatMode
from llama_index.embeddings import AzureOpenAIEmbedding, OpenAIEmbedding, OptimumEmbedding
from llama_index.embeddings.langchain import LangchainEmbedding
from llama_index.indices.base import BaseIndex
from llama_index.indices.composability import ComposableGraph
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.llms.base import LLM
from llama_index.llms.langchain import LangChainLLM
from llama_index.llms.openai import OpenAI
from llama_index.node_parser import NodeParser, SentenceSplitter
from llama_index.response.schema import RESPONSE_TYPE
from opentelemetry import trace

from ..config import EXPERIMENTS
from ..domain import SpaceKey
from ..model_selection.main import (
    LLM_MODEL_COLLECTIONS,
    ModelCapability,
    ModelUsageSettingsCollection,
    ModelVendor,
)
from .llamaindex_otel_callbackhandler import OtelCallbackHandler
from .metadata_extractors import DocqEntityExtractor, DocqMetadataExtractor
from .node_parsers import AsyncSimpleNodeParser
from .store import get_index_dir, get_models_dir

tracer = trace.get_tracer("docq.api.support.llm", docq.__version_str__)

# PROMPT_CHAT_SYSTEM = """
# You are an AI assistant helping a human to find information.
# Your conversation with the human is recorded in the chat history below.

# History:
# "{history}"
# """

# PROMPT_CHAT_HUMAN = "{input}"

PROMPT_QUESTION = """
You are an AI assistant helping a human to find information in a collection of documents.
You are given a question and a collection of documents.
You need to find the best answer to the question from the given collection of documents.
Your conversation with the human is recorded in the chat history below.

History:
"{history}"

Now continue the conversation with the human. If you do not know the answer, say "I don't know".
Human: {input}
Assistant:"""


ERROR_PROMPT = """
Examine the following error and provide a simple response for the user
Example: if the error is token limit based, simply say "Sorry, your question is too long, please try again with a shorter question"
if you can't understand the error, simply say "Sorry I cannot offer any assistance on the error message"
Make sure your response is in the first person context
ERROR: {error}
"""


# def _get_model() -> OpenAI:
#     return OpenAI(temperature=0, model_name="text-davinci-003")

@tracer.start_as_current_span(name="_init_local_models")
def _init_local_models() -> None:
    """Initialize local models."""
    for model_collection in LLM_MODEL_COLLECTIONS.values():
        for model_usage_settings in model_collection.model_usage_settings.values():
            if model_usage_settings.model_vendor == ModelVendor.HUGGINGFACE_OPTIMUM_BAAI:
                model_dir = get_models_dir(model_usage_settings.model_name, makedir=False)
                if not os.path.exists(model_dir):
                    model_dir = get_models_dir(model_usage_settings.model_name, makedir=True)
                    OptimumEmbedding.create_and_save_optimum_model(
                        model_usage_settings.model_name,
                        model_dir,
                    )

@tracer.start_as_current_span(name="_get_generation_model")
def _get_generation_model(model_settings_collection: ModelUsageSettingsCollection) -> LLM | None:
    model = None
    if model_settings_collection and model_settings_collection.model_usage_settings[ModelCapability.CHAT]:
        chat_model_settings = model_settings_collection.model_usage_settings[ModelCapability.CHAT]
        if chat_model_settings.model_vendor == ModelVendor.AZURE_OPENAI:
            model = AzureOpenAI(
                temperature=chat_model_settings.temperature,
                model=chat_model_settings.model_name,
                deployment_name=chat_model_settings.model_deployment_name,
                azure_endpoint=os.getenv("DOCQ_AZURE_OPENAI_API_BASE") or "",
                api_key=os.getenv("DOCQ_AZURE_OPENAI_API_KEY1") or "",
                #openai_api_type="azure",
                api_version=os.getenv("DOCQ_AZURE_OPENAI_API_VERSION") or "",
            )
            log.info("Chat model: using Azure OpenAI")
            _env_missing = not bool(
                os.getenv("DOCQ_AZURE_OPENAI_API_BASE")
                and os.getenv("DOCQ_AZURE_OPENAI_API_KEY1")
                and os.getenv("DOCQ_AZURE_OPENAI_API_VERSION")
            )
            if _env_missing:
                log.warning("Chat model: env var values missing.")
        elif chat_model_settings.model_vendor == ModelVendor.OPENAI:
            model = OpenAI(
                temperature=chat_model_settings.temperature,
                model=chat_model_settings.model_name,
                openai_api_key=os.getenv("DOCQ_OPENAI_API_KEY"),
            )
            log.info("Chat model: using OpenAI.")
            _env_missing = not bool(os.getenv("DOCQ_OPENAI_API_KEY"))
            if _env_missing:
                log.warning("Chat model: env var values missing")
        else:
            raise ValueError("Chat model: model settings with a supported model vendor not found.")

        return LangChainLLM(model)

@tracer.start_as_current_span(name="_get_embed_model")
def _get_embed_model(model_settings_collection: ModelUsageSettingsCollection) -> LLM | None:
    embedding_model = None
    result_model = None
    if model_settings_collection and model_settings_collection.model_usage_settings[ModelCapability.EMBEDDING]:
        embedding_model_settings = model_settings_collection.model_usage_settings[ModelCapability.EMBEDDING]

        with tracer.start_as_current_span(name=f"LangchainEmbedding.{embedding_model_settings.model_vendor}"):
            if embedding_model_settings.model_vendor == ModelVendor.AZURE_OPENAI:
                embedding_model = LangchainEmbedding(
                    AzureOpenAIEmbedding(
                        model=embedding_model_settings.model_name,
                        deployment=embedding_model_settings.model_deployment_name,
                        azure_endpoint=os.getenv("DOCQ_AZURE_OPENAI_API_BASE"),
                        api_key=os.getenv("DOCQ_AZURE_OPENAI_API_KEY1"),
                        #openai_api_type="azure",
                        api_version=os.getenv("DOCQ_AZURE_OPENAI_API_VERSION"),
                    ),
                    embed_batch_size=1,
                )
            elif embedding_model_settings.model_vendor == ModelVendor.OPENAI:
                embedding_model = LangchainEmbedding(
                    OpenAIEmbedding(
                        model=embedding_model_settings.model_name,
                        openai_api_key=os.getenv("DOCQ_OPENAI_API_KEY"),
                    ),
                    embed_batch_size=1,
                )
            elif embedding_model_settings.model_vendor == ModelVendor.HUGGINGFACE_OPTIMUM_BAAI:
                embedding_model = OptimumEmbedding(folder_name=get_models_dir(embedding_model_settings.model_name))
            else:
                # defaults
                embedding_model = LangchainEmbedding(OpenAIEmbedding())
            with tracer.start_as_current_span(name="LangChainLLM.init"):
                result_model = LangChainLLM(embedding_model)

    return result_model

@tracer.start_as_current_span(name="_get_default_storage_context")
def _get_default_storage_context() -> StorageContext:
    return StorageContext.from_defaults()


@tracer.start_as_current_span(name="_get_storage_context")
def _get_storage_context(space: SpaceKey) -> StorageContext:
    return StorageContext.from_defaults(persist_dir=get_index_dir(space))

@tracer.start_as_current_span(name="_get_service_context")
def _get_service_context(model_settings_collection: ModelUsageSettingsCollection) -> ServiceContext:
    log.debug(
        "EXPERIMENTS['INCLUDE_EXTRACTED_METADATA']['enabled']: %s", EXPERIMENTS["INCLUDE_EXTRACTED_METADATA"]["enabled"]
    )
    log.debug("EXPERIMENTS['ASYNC_NODE_PARSER']['enabled']: %s", EXPERIMENTS["ASYNC_NODE_PARSER"]["enabled"])

    _node_parser = None  # use default node parser
    if EXPERIMENTS["INCLUDE_EXTRACTED_METADATA"]["enabled"]:
        _node_parser = _get_node_parser(model_settings_collection)
        if EXPERIMENTS["ASYNC_NODE_PARSER"]["enabled"]:
            log.debug("loading async node parser.")
            _node_parser = _get_async_node_parser(model_settings_collection)
    else:
        _node_parser = SentenceSplitter.from_defaults(callback_manager=CallbackManager([OtelCallbackHandler(tracer_provider=trace.get_tracer_provider())]))

    return ServiceContext.from_defaults(
        llm=_get_generation_model(model_settings_collection),
        node_parser=_node_parser,
        embed_model=_get_embed_model(model_settings_collection),
        callback_manager=_node_parser.callback_manager,
    )

@tracer.start_as_current_span(name="_get_node_parser")
def _get_node_parser(model_settings_collection: ModelUsageSettingsCollection) -> NodeParser:
    # metadata_extractor = MetadataExtractor(
    #     extractors=[

    #         KeywordExtractor(llm=_get_generation_model(model_settings_collection), keywords=5),
    #         EntityExtractor(label_entities=True, device="cpu"),
    #         # CustomExtractor()
    #     ],
    # )

    node_parser = SentenceSplitter.from_defaults(callback_manager=CallbackManager([OtelCallbackHandler(tracer_provider=trace.get_tracer_provider())]),)

    return node_parser

@tracer.start_as_current_span(name="_get_async_node_parser")
def _get_async_node_parser(model_settings_collection: ModelUsageSettingsCollection) -> AsyncSimpleNodeParser:

    metadata_extractor = DocqMetadataExtractor(
        extractors=[
            #KeywordExtractor(llm=_get_chat_model_using_langchain(model_settings_collection), keywords=5),
        ],
        async_extractors=[
            DocqEntityExtractor(label_entities=True, device="cpu"),
        ]
    )
    #TODO: if async node parser
    node_parser = AsyncSimpleNodeParser.from_defaults(  # SimpleNodeParser is the default when calling ServiceContext.from_defaults()

    )

    return node_parser


@tracer.start_as_current_span(name="_load_index_from_storage")
def _load_index_from_storage(space: SpaceKey, model_settings_collection: ModelUsageSettingsCollection) -> BaseIndex:
    # set service context explicitly for multi model compatibility
    sc = _get_service_context(model_settings_collection)
    return load_index_from_storage(
        storage_context=_get_storage_context(space), service_context=sc, callback_manager=sc.callback_manager
    )

@tracer.start_as_current_span(name="run_chat")
def run_chat(input_: str, history: str, model_settings_collection: ModelUsageSettingsCollection) -> AgentChatResponse:
    """Chat directly with a LLM with history."""
    # prompt = ChatPromptTemplate.from_messages(
    #     [
    #         SystemMessagePromptTemplate.from_template(PROMPT_CHAT_SYSTEM),
    #         HumanMessagePromptTemplate.from_template(PROMPT_CHAT_HUMAN),
    #     ]
    # )
    # output = _get_chat_model()(prompt.format_prompt(history=history, input=input_).to_messages())
    engine = SimpleChatEngine.from_defaults(service_context=_get_service_context(model_settings_collection))
    output = engine.chat(input_)

    log.debug("(Chat) Q: %s, A: %s", input_, output)
    return output


def run_ask(
    input_: str,
    history: str,
    model_settings_collection: ModelUsageSettingsCollection,
    space: SpaceKey | None = None,
    spaces: list[SpaceKey] | None = None,
) -> RESPONSE_TYPE | AGENT_CHAT_RESPONSE_TYPE:
    """Ask questions against existing index(es) with history."""
    log.debug("exec: runs_ask()")
    if spaces is not None and len(spaces) > 0:
        log.debug("runs_ask(): spaces count: %s", len(spaces))
        # With additional spaces likely to be combining a number of shared spaces.
        indices = []
        summaries = []
        output = _default_response()
        all_spaces = spaces + ([space] if space else [])
        for s_ in all_spaces:
            try:
                index_ = _load_index_from_storage(s_, model_settings_collection)

                log.debug("run_chat(): %s, %s", index_.index_id, s_.summary)
                indices.append(index_)
                summaries.append(s_.summary) if s_.summary else summaries.append("")

            except Exception as e:
                log.warning(
                    "Index for space '%s' failed to load, skipping. Maybe the index isn't created yet. Error message: %s",
                    s_,
                    e,
                )
                continue

        log.debug("number summaries: %s", len(summaries))
        try:
            graph = ComposableGraph.from_indices(
                SummaryIndex,
                indices,
                index_summaries=summaries,
                service_context=_get_service_context(model_settings_collection),
            )
            output = graph.as_query_engine().query(PROMPT_QUESTION.format(history=history, input=input_))

            log.debug("(Ask combined spaces %s) Q: %s, A: %s", all_spaces, input_, output)
        except Exception as e:
            log.error(
                "Failed to create ComposableGraph. Maybe there was an issue with one of the Space indexes. Error message: %s",
                e,
            )
    else:
        log.debug("runs_ask(): space None or zero. Assuming personal ASK.")
        # No additional spaces i.e. likely to be against a user's documents in their personal space.
        if space is None:
            log.debug("runs_ask(): space is None. executing run_chat(), not ASK.")
            output = run_chat(input_=input_, history=history, model_settings_collection=model_settings_collection)
        else:
            index = _load_index_from_storage(space=space, model_settings_collection=model_settings_collection)
            engine = index.as_chat_engine(
                verbose=True,
                similarity_top_k=3,
                vector_store_query_mode="default",
                chat_mode=ChatMode.CONDENSE_QUESTION,
            )
            output = engine.chat(input_)
            log.debug("(Ask %s w/o shared spaces) Q: %s, A: %s", space, input_, output)

    return output

@tracer.start_as_current_span(name="_default_response")
def _default_response() -> Response:
    """A default response incase of any failure."""
    return Response("I don't know.")

@tracer.start_as_current_span(name="query_error")
def query_error(error: Exception, model_settings_collection: ModelUsageSettingsCollection) -> Response:
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
