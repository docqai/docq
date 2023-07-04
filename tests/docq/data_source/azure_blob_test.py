import unittest  # noqa: D100
from unittest.mock import MagicMock, patch

from azure_blob import AzureBlob


class TestAzureBlob(unittest.TestCase):  # noqa: D101
    def setUp(self) -> None:  # noqa: D102
        self.azure_blob = AzureBlob()

    def test_get_config_keys(self) -> None:  # noqa: D102
        config_keys = self.azure_blob.get_config_keys()
        assert len(config_keys) == 3
        assert config_keys[0].key == "account_url"
        assert config_keys[1].key == "container_name"
        assert config_keys[2].key == "credential"

    @patch("azure_blob.download_loader")
    def test_load(self, mock_download_loader):
        mock_loader = MagicMock()
        mock_download_loader.return_value = mock_loader

        space = "test_space"
        configs = {
            "account_url": "test_account_url",
            "container_name": "test_container_name",
            "credential": "test_credential",
        }

        documents = self.azure_blob.load(space, configs)

        mock_download_loader.assert_called_once_with("AzStorageBlobReader")
        mock_loader.assert_called_once_with(
            container_name=configs["container_name"],
            account_url=configs["account_url"],
            credential=configs["credential"],
        )
        assert documents == mock_loader.load_data.return_value

    @patch("azure_blob.ContainerClient")
    def test_get_document_list(self, mock_container_client):
        mock_blobs = [
            MagicMock(name="test_blob1", last_modified="2022-01-01", size=100),
            MagicMock(name="test_blob2", last_modified="2022-01-02", size=200),
        ]
        mock_container_client.return_value.list_blobs.return_value = mock_blobs

        space = "test_space"
        configs = {
            "account_url": "test_account_url",
            "container_name": "test_container_name",
            "credential": "test_credential",
        }

        document_list = self.azure_blob.get_document_list(space, configs)

        mock_container_client.assert_called_once_with(
            configs["account_url"], configs["container_name"], configs["credential"]
        )
        mock_container_client.return_value.list_blobs.assert_called_once_with()
        assert document_list == [("test_blob1", "2022-01-01", 100), ("test_blob2", "2022-01-02", 200)]

    @patch("azure_blob.ContainerClient")
    def test_get_document_list_exception(self, mock_container_client):
        mock_container_client.side_effect = Exception("test_exception")

        space = "test_space"
        configs = {
            "account_url": "test_account_url",
            "container_name": "test_container_name",
            "credential": "test_credential",
        }

        with self.assertRaises(Exception) as cm:
            self.azure_blob.get_document_list(space, configs)

        mock_container_client.assert_called_once_with(
            configs["account_url"], configs["container_name"], configs["credential"]
        )
        assert str(cm.exception) == "Ooops! something went wrong. Please check your datasource credentials and try again."
