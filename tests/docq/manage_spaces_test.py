from unittest.mock import Mock, patch

from docq.config import SpaceType
from docq.domain import SpaceKey
from docq.manage_documents import reindex
from llama_index import GPTVectorStoreIndex


def test_reindex():
    with patch("docq.manage_spaces._persist_index") as mock_persist_index, patch(
        "docq.manage_spaces._create_index"
    ) as mock_create_index:
        mock_index = Mock(GPTVectorStoreIndex)
        mock_create_index.return_value = mock_index

        arg_space_key = SpaceKey(SpaceType.PERSONAL, 1234)

        reindex(arg_space_key)

        mock_persist_index.assert_called_once_with(mock_index, arg_space_key)
