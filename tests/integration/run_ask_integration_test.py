from unittest.mock import patch

import pytest
from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_assistants import get_assistant_or_default
from docq.manage_indices import _create_vector_index
from docq.model_selection.main import get_model_settings_collection
from docq.support import llm
from llama_index.core.base.response.schema import Response
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.schema import Document

# NOTE: if you run just this test directly it will fail because the env vars will not load.


@pytest.fixture
def setup_environment():
    llm._init_local_models()  # download local models needed for embeddings


def test_run_ask2_query_pipeline_logic(setup_environment):
    """Test shared ask against a single space. Tunning a query through the pipeline without mocking."""
    input_ = "Who is the CEO of banging_the_bang_bang inc?"
    history = [
        ChatMessage(role=MessageRole.USER, content="Hello"),
        ChatMessage(role=MessageRole.ASSISTANT, content="Hi there!"),
    ]

    assistant = get_assistant_or_default()
    model_settings_collection = get_model_settings_collection(assistant.llm_settings_collection_key)

    # spaces = cast(List[SpaceKey], [MagicMock(spec=SpaceKey)])

    doc1 = Document(doc_id="1", text="The capital of France is Paris.")
    doc2 = Document(doc_id="2", text="The capital of Germany is Berlin.")
    doc2 = Document(
        doc_id="2", text="Mr bingbongbob is the CEO or banging_the_bang_bang inc. They were established in 1999."
    )
    documents = [doc1, doc2]

    result_index = _create_vector_index(documents, model_settings_collection)
    space1 = SpaceKey(type_=SpaceType.SHARED, id_=9, org_id=9999, summary="test space")
    spaces = [space1]

    with patch("docq.support.llm.load_indices_from_storage", return_value=[result_index]):
        response = llm.run_ask2(input_, history, model_settings_collection, assistant, spaces)

        assert isinstance(response, Response)
        assert response.response is not None
        assert "bingbongbob" in response.response
