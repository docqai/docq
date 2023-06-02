from unittest.mock import MagicMock, Mock, patch

import pytest
from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.support.llm import reindex, run_ask, run_chat
from docq.support.store import get_index_dir
from langchain.chat_models import ChatOpenAI
from langchain.llms import OpenAI
from llama_index import GPTVectorStoreIndex, ServiceContext, StorageContext
from langchain.schema import BaseMessage
from llama_index.query_engine.graph_query_engine import ComposableGraphQueryEngine
from llama_index.indices.composability import ComposableGraph


# def test_run_ask_with_personal_space_only():
#     with patch("docq.support.llm._get_load_index_from_storage") as mock_load_index, patch(
#         "docq.support.llm._get_service_context"
#     ) as mock_get_service_context:
#         mock_index = MagicMock(GPTVectorStoreIndex)
#         mock_load_index.return_value = mock_index

#         mock_service_context = MagicMock(ServiceContext)
#         mock_get_service_context.return_value = mock_service_context

#         run_ask("My ask", "My chat history", SpaceKey(SpaceType.PERSONAL, 1234))
#         mock_index.as_query_engine().query().assert_called_once()


# def test_run_ask_with_shared_spaces():
#     with patch("docq.support.llm._load_index_from_storage") as mock_load_index, patch(
#         "docq.support.llm._get_service_context"
#     ) as mock_get_service_context, patch("llama_index.indices.composability.ComposableGraph") as mock_graph:
#         mocked_index = Mock(GPTVectorStoreIndex)
#         mock_load_index.return_value = mocked_index
#         mocked_query = Mock()
#         mocked_index.query = mocked_query
#         mocked_query.return_value = Mock()
#         mocked_graph = Mock(ComposableGraph)
#         mock_graph.from_indices.return_value = mocked_graph
#         mocked_engine = Mock(ComposableGraphQueryEngine)
#         mocked_graph.as_query_engine = mocked_engine

#         personal_space = SpaceKey(SpaceType.PERSONAL, 1234)
#         shared_spaces = [SpaceKey(SpaceType.SHARED, 9999), SpaceKey(SpaceType.SHARED, 8888)]

#         run_ask(
#             "My ask",
#             "My chat history",
#             personal_space,
#             shared_spaces,
#         )
#         mock_load_index.assert_called_once_with(personal_space)
#         mock_load_index.assert_called_once_with(shared_spaces[0])
#         mock_load_index.assert_called_once_with(shared_spaces[1])
#         mocked_query.assert_called()
#         mock_get_service_context.assert_called_once()
#         mock_graph.from_indices.assert_called_once()
#         mocked_engine.query.assert_called_once()


def test_run_chat():
    with patch("docq.support.llm._get_chat_model") as mock_get_chat_model:
        mock_chat_openai = Mock(ChatOpenAI)
        mock_get_chat_model.return_value = mock_chat_openai
        mock_chat_openai.return_value = "LLM response"

        response = run_chat("My ask", "My chat history")
        assert response == "LLM response"


def test_reindex():
    with patch("docq.support.llm._persist_index") as mock_persist_index, patch(
        "docq.support.llm._create_index"
    ) as mock_create_index:
        mock_index = Mock(GPTVectorStoreIndex)
        mock_create_index.return_value = mock_index

        arg_space_key = SpaceKey(SpaceType.PERSONAL, 1234)

        reindex(arg_space_key)
        mock_create_index.assert_called_once_with(arg_space_key)
        mock_persist_index.assert_called_once_with(mock_index, arg_space_key)
