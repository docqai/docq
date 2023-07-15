"""Functions for utilising LLMs."""

import logging as log

from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage
from llama_index import (
    GPTListIndex,
    GPTVectorStoreIndex,
    LLMPredictor,
    Response,
    ServiceContext,
    StorageContext,
    load_index_from_storage,
)
from llama_index.chat_engine import SimpleChatEngine
from llama_index.indices.composability import ComposableGraph
from llama_index.node_parser import SimpleNodeParser
from llama_index.node_parser.extractors import (
    KeywordExtractor,
    MetadataExtractor,
    # MetadataFeatureExtractor,
    QuestionsAnsweredExtractor,
    SummaryExtractor,
    TitleExtractor,
)

from ..config import EXPERIMENTS
from ..domain import SpaceKey
from .store import get_index_dir

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


def _get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(temperature=0, model="gpt-3.5-turbo")


def _get_llm_predictor() -> LLMPredictor:
    return LLMPredictor(llm=_get_chat_model())


def _get_default_storage_context() -> StorageContext:
    return StorageContext.from_defaults()


def _get_storage_context(space: SpaceKey) -> StorageContext:
    return StorageContext.from_defaults(persist_dir=get_index_dir(space))


def _get_service_context() -> ServiceContext:
    log.debug(
        "EXPERIMENTS['INCLUDE_EXTRACTED_METADATA']['enabled']: %s", EXPERIMENTS["INCLUDE_EXTRACTED_METADATA"]["enabled"]
    )
    if EXPERIMENTS["INCLUDE_EXTRACTED_METADATA"]["enabled"]:
        return ServiceContext.from_defaults(llm_predictor=_get_llm_predictor(), node_parser=_get_node_parser())
    else:
        return ServiceContext.from_defaults(llm_predictor=_get_llm_predictor())


def _get_node_parser() -> SimpleNodeParser:
    metadata_extractor = MetadataExtractor(
        extractors=[
            TitleExtractor(nodes=5),
            QuestionsAnsweredExtractor(questions=3),
            SummaryExtractor(summaries=["prev", "self"]),
            KeywordExtractor(keywords=10),
            # CustomExtractor()
        ],
    )

    node_parser = (
        SimpleNodeParser.from_defaults(  # SimpleNodeParser is the default when calling ServiceContext.from_defaults()
            metadata_extractor=metadata_extractor,  # adds extracted metatdata as extra_info
        )
    )

    return node_parser


def _load_index_from_storage(space: SpaceKey) -> GPTVectorStoreIndex:
    return load_index_from_storage(storage_context=_get_storage_context(space))


def run_chat(input_: str, history: str) -> BaseMessage:
    """Chat directly with a LLM with history."""
    # prompt = ChatPromptTemplate.from_messages(
    #     [
    #         SystemMessagePromptTemplate.from_template(PROMPT_CHAT_SYSTEM),
    #         HumanMessagePromptTemplate.from_template(PROMPT_CHAT_HUMAN),
    #     ]
    # )
    # output = _get_chat_model()(prompt.format_prompt(history=history, input=input_).to_messages())
    engine = SimpleChatEngine.from_defaults(service_context=_get_service_context())
    output = engine.chat(input_)

    log.debug("(Chat) Q: %s, A: %s", input_, output)
    return output


def run_ask(input_: str, history: str, space: SpaceKey = None, spaces: list[SpaceKey] = None) -> Response:
    """Ask questions against existing index(es) with history."""
    if spaces is not None and len(spaces) > 0:
        # With additional spaces likely to be combining a number of shared spaces.
        indices = []
        summaries = []
        all_spaces = spaces + ([space] if space else [])
        for s_ in all_spaces:
            index_ = _load_index_from_storage(s_)
            summary_ = index_.as_query_engine().query(
                "What is the summary of all the documents?"
            )  # note: we might not need to do this any longer because summary is added as node metadata.
            indices.append(index_)

            summaries.append(summary_.response)
            try:
                index_ = _load_index_from_storage(s_)
                summary_ = index_.as_query_engine().query(
                    "What is the summary of all the documents?"
                )  # note: we might not need to do this any longer because summary is added as node metadata.
                indices.append(index_)

                summaries.append(summary_.response)
            except Exception as e:
                log.warning(
                    "Index for space '%s' failed to load. Maybe the index isn't created yet. Error message: %s", s_, e
                )
                continue

        log.debug("number summaries: %s", len(summaries))
        graph = ComposableGraph.from_indices(
            GPTListIndex, indices, index_summaries=summaries, service_context=_get_service_context()
        )
        output = graph.as_query_engine().query(PROMPT_QUESTION.format(history=history, input=input_))

        log.debug("(Ask combined spaces %s) Q: %s, A: %s", all_spaces, input_, output)
    else:
        # No additional spaces i.e. likely to be against a user's documents in their personal space.
        if space is None:
            output = run_chat(input_, history)
        else:
            index = _load_index_from_storage(space)
            engine = index.as_chat_engine(verbose=True, similarity_top_k=3, vector_store_query_mode="default")
            output = engine.chat(input_)
            log.debug("(Ask %s w/o shared spaces) Q: %s, A: %s", space, input_, output)

    return output


def _default_response() -> Response:
    """A default response incase of any failure."""
    return Response("I don't know.")


def query_error(error: Exception) -> Response:
    """Query for a response to an error message."""
    try:  # Try re-prompting with the AI
        log.exception("Error: %s", error)
        input_ = ERROR_PROMPT.format(error=error)
        return SimpleChatEngine.from_defaults(service_context=_get_service_context()).chat(input_)
    except Exception as error:
        log.exception("Error: %s", error)
        return _default_response()
