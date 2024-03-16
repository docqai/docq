"""Data source for scrapping a website."""

import logging as log
from datetime import datetime
from typing import List, Optional, Self

from llama_index.core.schema import Document

from ..domain import ConfigKey, SourcePageType, SpaceKey
from ..support.store import get_index_dir
from .main import DocumentMetadata, SpaceDataSourceWebBased
from .support.web_extracting import BeautifulSoupWebReader, GenericTextExtractor


class WebScraper(SpaceDataSourceWebBased):
    """Data scraped from a website."""

    def __init__(self, alternative_name: Optional[str] = None) -> None:
        """Initialize the data source."""
        super().__init__("Web Scraper" if alternative_name is None else alternative_name)

    def get_config_keys(self: Self) -> List[ConfigKey]:
        """Get the config keys for web scraper."""
        return [
            ConfigKey(
                "source_page_type",
                "Source Page Type",
                False,
                False,
                None,
                {
                    "type": "selectbox",
                    "select_box_options": {
                        SourcePageType.index_page.name: SourcePageType.index_page.value,
                        SourcePageType.page_list.name: SourcePageType.page_list.value,
                    },
                },
            ),
            ConfigKey("website_url", "Website URL"),
            ConfigKey("extractor_name", "Extractor Template Name", True),
            ConfigKey(
                "include_filter",
                "Include Filter Regex",
                True,
                ref_link="Python Regex. URLs that match will be included in the index.",
            ),
        ]

    def load(self: Self, space: SpaceKey, configs: dict) -> List[Document]:
        """Extract text from web pages on a website and load each page as a Document."""
        _documents = []
        try:
            log.debug("configs: %s", configs)
            persist_path = get_index_dir(space)

            bs_web_reader = self._initiate_web_reader(space, configs)

            source_page_type_str = configs.get("source_page_type")
            print("source_page_type: ", source_page_type_str)
            source_page_type = (
                SourcePageType[source_page_type_str[0]] if source_page_type_str else SourcePageType.index_page
            )

            _documents = bs_web_reader.load_data(
                urls=configs["website_url"].split(","),
                include_filter=configs["include_filter"],
                source_page_type=source_page_type,
            )

            document_list = bs_web_reader.get_document_list()

            log.debug("created document list: %s", document_list)
            self._save_document_list(document_list, persist_path, self._DOCUMENT_LIST_FILENAME)

            log.info("web doc count %d", len(_documents))
        except Exception as e:
            log.error("Error loading web documents", e)

        webscaper_metadata_keys = []
        exclude_embed_metadata_keys_ = [
            str(DocumentMetadata.SPACE_ID.name).lower(),
            str(DocumentMetadata.SPACE_TYPE.name).lower(),
            str(DocumentMetadata.SOURCE_URI.name).lower(),
            str(DocumentMetadata.DATA_SOURCE_NAME.name).lower(),
            str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower(),
            str(DocumentMetadata.INDEXED_ON.name).lower(),
        ]
        exclude_embed_metadata_keys_.extend(webscaper_metadata_keys)

        excluded_llm_metadata_keys_ = [
            str(DocumentMetadata.SPACE_ID.name).lower(),
            str(DocumentMetadata.SPACE_TYPE.name).lower(),
            str(DocumentMetadata.DATA_SOURCE_NAME.name).lower(),
            str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower(),
            str(DocumentMetadata.INDEXED_ON.name).lower(),
        ]

        return self._add_exclude_metadata_keys(_documents, exclude_embed_metadata_keys_, excluded_llm_metadata_keys_)

    def _initiate_web_reader(self: Self, space: SpaceKey, configs: dict) -> BeautifulSoupWebReader:
        """Initialize the web reader."""

        def lambda_metadata(x: str) -> dict:
            return {
                str(DocumentMetadata.SPACE_ID.name).lower(): space.id_,
                str(DocumentMetadata.SPACE_TYPE.name).lower(): space.type_.name,
                str(DocumentMetadata.DATA_SOURCE_NAME.name).lower(): self.get_name(),
                str(DocumentMetadata.DATA_SOURCE_TYPE.name).lower(): self.__class__.__base__.__name__,
                str(DocumentMetadata.INDEXED_ON.name).lower(): datetime.timestamp(datetime.now().utcnow()),
            }

        return BeautifulSoupWebReader(
            {
                "default": GenericTextExtractor(),
            },
            lambda_metadata,
        )
