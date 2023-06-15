"""Functions for utilising LLMs."""

import logging as log

from langchain.chat_models import ChatOpenAI

# from langchain.llms import OpenAI
# from langchain.prompts.chat import (
#     ChatPromptTemplate,
#     HumanMessagePromptTemplate,
#     SystemMessagePromptTemplate,
# )
from langchain.schema import BaseMessage
from llama_index import (
    GPTListIndex,
    GPTVectorStoreIndex,
    LLMPredictor,
    Response,
    ServiceContext,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)
from llama_index.chat_engine import CondenseQuestionChatEngine, SimpleChatEngine
from llama_index.indices.composability import ComposableGraph

from ..domain import SpaceKey
from .store import get_index_dir, get_upload_dir

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
    return ServiceContext.from_defaults(llm_predictor=_get_llm_predictor())


def _create_index(space: SpaceKey) -> GPTVectorStoreIndex:
    docs = SimpleDirectoryReader(get_upload_dir(space)).load_data()
    # Use default storage and service context to initialise index purely for persisting
    return GPTVectorStoreIndex.from_documents(
        docs, storage_context=_get_default_storage_context(), service_context=_get_service_context()
    )


def _load_index_from_storage(space: SpaceKey) -> GPTVectorStoreIndex:
    return load_index_from_storage(storage_context=_get_storage_context(space))


def _persist_index(index: GPTVectorStoreIndex, space: SpaceKey) -> None:
    index.storage_context.persist(persist_dir=get_index_dir(space))


def reindex(space: SpaceKey) -> None:
    """Reindex documents in a space."""
    index = _create_index(space)
    _persist_index(index, space)


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


def run_ask(input_: str, history: str, space: SpaceKey, spaces: list[SpaceKey] = None) -> Response:
    """Ask questions against existing index(es) with history."""
    if spaces is not None and len(spaces) > 0:
        # With additional spaces likely to be combining a number of shared spaces.
        indices = []
        summaries = []
        for s_ in spaces + [space]:
            index_ = _load_index_from_storage(s_)
            summary_ = index_.as_query_engine().query("What is the summary of all the documents?")
            indices.append(index_)
            summaries.append(summary_)
        graph = ComposableGraph.from_indices(
            GPTListIndex, indices, index_summaries=summaries, service_context=_get_service_context()
        )
        output = graph.as_query_engine().query(PROMPT_QUESTION.format(history=history, input=input_))
    else:
        # No additional spaces i.e. likely to be against a user's documents in their personal space.
        index = _load_index_from_storage(space)
        engine = index.as_chat_engine(verbose=True, similarity_top_k=3, vector_store_query_mode="default")
        output = engine.chat(input_)

    log.debug("(Ask w/ spaces ) Q: %s, A: %s", spaces, input_, output)
    return output
