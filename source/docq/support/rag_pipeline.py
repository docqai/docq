"""Orchestrates the RAG pipeline."""

import inspect
from typing import Any, Callable, Dict, List, Optional, Tuple

from docq.domain import Assistant
from llama_index.core.indices.base import BaseIndex
from llama_index.core.llms import LLM, ChatMessage, ChatResponse, MessageRole
from llama_index.core.schema import NodeWithScore
from llama_index.retrievers.bm25 import BM25Retriever


def search_stage(
    user_query: str,
    indices: List[BaseIndex],
    reranker: Callable[[Dict[str, List[NodeWithScore]], Optional[List[str]]], List[NodeWithScore]]
    | Callable[[Dict[str, List[NodeWithScore]]], List[NodeWithScore]],
    query_preprocessor: Optional[Callable[[str], List[str]]] = None,
    top_k: int = 10,
    enable_debug: Optional[bool] = False,
) -> Tuple[List[NodeWithScore], Dict[str, Any]]:
    """Search stage of the RAG pipeline.

    Args:
        user_query (str): The user query.
        indices (List[BaseIndex]): The list of indices to search.
        reranker (Callable[[Dict[str, List[NodeWithScore]], Optional[List[str]]], List[NodeWithScore]]): The reranker to use. `func(search_results: List[List[NodeWithScore]], user_query: Optional[List[str]] = None) -> List[NodeWithScore]`. If not provided, a default reranker that uses X is used.
        query_preprocessor (Optional[Callable[[str], List[str]]]): The preprocessor to use. `func(user_query: str) -> List[str]`. Defaults to no preprocessing.
        top_k (int): The number of results to return per search.

    Returns:
        List[NodeWithScore]: The reduced and reranked search results.
    """
    debug: dict[str, Any] = {}
    if reranker is None:
        raise ValueError("Reranker is required")

    _vector_retrievers = {}
    _bm25_retrievers = {}

    # 1. Prepare retrievers
    for i, index in enumerate(indices):
        _vector_retrievers[f"vector_{index.index_id}_{i}"] = index.as_retriever(similarity_top_k=top_k)
        _bm25_retrievers[f"bm25_{index.index_id}_{i}"] = BM25Retriever.from_defaults(
            docstore=index.docstore, similarity_top_k=top_k
        )

    # 2. Preprocess user query if preprocessor is provided
    processed_queries = query_preprocessor(user_query) if query_preprocessor else [user_query]

    # 3. Run the list of queries through each retriever
    vector_results = {}
    bm25_results = {}

    for i, query in enumerate(processed_queries):
        for key, vr in _vector_retrievers.items():
            vector_results[f"{key}_query_{i}"] = vr.retrieve(query)

        for key, br in _bm25_retrievers.items():
            bm25_results[f"{key}_query_{i}"] = br.retrieve(query)

    # 4. Combine results
    combined_results = {**vector_results, **bm25_results}

    if callable(reranker):
        reranker_params = inspect.signature(reranker).parameters
        if len(reranker_params) == 2:
            reranked_results = reranker(combined_results, processed_queries)  # type: ignore
        elif len(reranker_params) == 1:
            reranked_results = reranker(combined_results)  # type: ignore
        else:
            raise ValueError("Reranker function must accept either one or two arguments")
    else:
        raise TypeError("Reranker must be a callable")

    if enable_debug:
        for key, value in vector_results.items():
            debug[key] = value
        for key, value in bm25_results.items():
            debug[key] = value
        debug["reranked_results"] = reranked_results
        debug["processed_queries"] = processed_queries

    return (reranked_results, debug)


def generation_stage(
    user_query: str,
    assistant: Assistant,
    search_results: List[NodeWithScore],
    message_history: List[ChatMessage],
    llm: LLM,
    enable_debug: Optional[bool] = False,
) -> Tuple[ChatResponse, Dict[str, Any]]:
    """Generation stage of the RAG pipeline.

    Args:
        user_query (str): The user query.
        assistant (Assistant): The assistant.
        search_results (List[NodeWithScore]): The search results.
        message_history (List[ChatMessage]): The message history.
        llm (LLM): The LLM.

    Returns:
        ChatResponse: The response from the LLM.
    """
    debug: dict[str, Any] = {}
    # build system message
    system_message = ChatMessage(role=MessageRole.SYSTEM, content=assistant.system_message_content)

    # build query message
    query_message = ChatMessage(
        role=MessageRole.USER,
        content=assistant.user_prompt_template_content.format(
            context_str="\n".join([node.text for node in search_results]),
            query_str=user_query,
        ),
    )

    chat_messages = [system_message] + message_history + [query_message]

    # Generate response
    response = llm.chat(messages=chat_messages)

    if enable_debug:
        debug["system_message"] = system_message
        debug["user_prompt_template_content"] = assistant.user_prompt_template_content
        debug["query_message"] = query_message
        debug["search_results"] = search_results

    # TODO: Add source references to the response

    return (response, debug)


def rag_pipeline(
    user_query: str,
    indices: List[BaseIndex],
    assistant: Assistant,
    message_history: List[ChatMessage],
    llm: LLM,
    reranker: Callable[[Dict[str, List[NodeWithScore]], Optional[List[str]]], List[NodeWithScore]]
    | Callable[[Dict[str, List[NodeWithScore]]], List[NodeWithScore]],
    query_preprocessor: Optional[Callable[[str], List[str]]] = None,
    top_k: int = 10,
) -> ChatResponse:
    """Orchestrates the RAG pipeline.

    Args:
        user_query (str): The user query.
        indices (List[BaseIndex]): The list of indices to search.
        assistant (Assistant): The assistant.
        message_history (List[ChatMessage]): The message history.
        llm (LLM): The LLM.
        reranker (Callable[[Dict[str, List[NodeWithScore]], Optional[List[str]]], List[NodeWithScore]]): The reranker to use. `func(search_results: List[List[NodeWithScore]], user_query: Optional[str] = None) -> List[NodeWithScore]`. If not provided, a default reranker that uses X is used.
        query_preprocessor (Optional[Callable[[str], List[str]]]): The preprocessor to use. `func(user_query: str) -> List[str]`. Defaults to no preprocessing.
        top_k (int): The number of results to return per search.

    Returns:
        ChatResponse: The response from the LLM.
    """
    # Search stage
    search_results, debug = search_stage(
        user_query=user_query, indices=indices, reranker=reranker, query_preprocessor=query_preprocessor, top_k=top_k
    )

    # Generation stage
    response, debug = generation_stage(
        user_query=user_query,
        search_results=search_results,
        message_history=message_history,
        assistant=assistant,
        llm=llm,
    )

    return response
