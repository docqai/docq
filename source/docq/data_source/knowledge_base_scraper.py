"""Data source for scrapping articles from a knowledge base."""

import logging as log
from typing import List

from ..domain import ConfigKey, SpaceKey
from .main import DocumentMetadata
from .support.web_extracting import BeautifulSoupWebReader, GenericKnowledgeBaseExtractor, GenericTextExtractor
from .web_scraper import WebScraper


class KnowledgeBaseScraper(WebScraper):
    """Data source for scrapping articles from a knowledge base."""

    _DOCUMENT_LIST_FILENAME = "document_list.json"

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("Knowledge Base Scraper")

    def get_config_keys(self) -> List[ConfigKey]:
        """Get the config keys for knowledge base scraper."""
        keys = super().get_config_keys()
        keys.extend(
            [
                ConfigKey(
                    "title_css_selector",
                    "Title CSS Selector",
                    True,
                    ref_link="Space separated CSS class names to filter on.",
                ),
                ConfigKey("subtitle_css_selector", "Subtitle CSS Selector", True),
            ]
        )
        return keys

    def _initiate_web_reader(self, space: SpaceKey, configs: dict) -> BeautifulSoupWebReader:
        """Initialize the web reader."""

        def lambda_metadata(x: str) -> dict:
            return {
                DocumentMetadata.SPACE_ID.name: space.id_,
                DocumentMetadata.SPACE_TYPE.name: space.type_.name,
                DocumentMetadata.DATA_SOURCE_NAME.name: self.get_name(),
                DocumentMetadata.DATA_SOURCE_TYPE.name: self.__class__.__base__.__name__,
            }

        return BeautifulSoupWebReader(
            {
                "default": GenericTextExtractor(),
                "GenericKnowledgeBaseExtractor": GenericKnowledgeBaseExtractor(
                    title_css_selector=configs["title_css_selector"],
                    subtitle_css_selector=configs["subtitle_css_selector"],
                ),
            },
            lambda_metadata,
        )
