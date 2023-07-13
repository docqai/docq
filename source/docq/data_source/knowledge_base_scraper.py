"""Data source for scrapping articles from a Knowledgebase systen."""

import json
import logging as log
import os
from typing import List

from llama_index import Document

from ..config import SpaceDataSourceType
from ..domain import ConfigKey, SpaceKey
from .main import DocumentMetadata, SpaceDataSourceWebBased
from .web_scraper import BaseTextExtractor, BeautifulSoupWebReader


class KnowledgeBaseScraper(SpaceDataSourceWebBased):
    """Data source for scrapping articles from a Knowledgebase systen."""

    _DOCUMENT_LIST_FILENAME = "document_list.json"

    def __init__(self) -> None:
        """Initialize the data source.

        Args:
            persist_path (str): The path to the directory where the document list for the data source will persist its data.
        """
        super().__init__(
            SpaceDataSourceType.KNOWLEDGE_BASE_SCRAPER.value, SpaceDataSourceType.KNOWLEDGE_BASE_SCRAPER.name
        )
        self._document_list = []

    def get_config_keys(self) -> List[ConfigKey]:
        """Get the config keys for web scraper."""
        return [
            ConfigKey("website_url", "Website URL"),
            ConfigKey("extractor_name", "Extractor Template Name"),
            ConfigKey(
                "include_filter",
                "Include Filter Regex",
                ref_link="Python Regex. URLs that match will be included in the index.",
            ),
            ConfigKey(
                "title_css_selector",
                "Title CSS Selector",
                ref_link="Space separated CSS class names to filter on.",
            ),
            ConfigKey("subtitle_css_selector", "Subtitle CSS Selector"),
        ]

    def load(self, space: SpaceKey, configs: dict, persist_path: str) -> List[Document]:
        """Extract text from web pages on a website and load each page as a Document."""

        def lambda_metadata(x: str) -> dict:
            return {
                DocumentMetadata.SPACE_ID.name: space.id_,
                DocumentMetadata.SPACE_TYPE.name: space.type_.name,
            }

        try:
            log.debug("config: %s", configs)

            bs_web_reader = BeautifulSoupWebReader(
                website_metadata=lambda_metadata,
                website_extractor={
                    "GenericKnowledgeBaseExtractor": GenericKnowledgeBaseExtractor(
                        title_css_selector=configs["title_css_selector"],
                        subtitle_css_selector=configs["subtitle_css_selector"],
                    )
                },
            )
            documents = bs_web_reader.load_data(
                urls=[configs["website_url"]],
                custom_hostname=configs["extractor_name"],
                include_filter=configs["include_filter"],
            )

            self._document_list = bs_web_reader.get_document_list()
            log.debug("_document_list: %s", self._document_list)
            self._save_document_list(persist_path, self._DOCUMENT_LIST_FILENAME)

            log.info(f"web doc count {len(documents)}")  # noqa: G004
        except Exception as e:
            log.error("WebScraper: Error loading web documents", e)
            # log.info(documents)
        return documents

    def get_document_list(self, space: SpaceKey, configs: dict, persist_path: str) -> list[tuple[str, int, int]]:
        """Returns a list of tuples containing the name, creation time, and size (Mb) of each document in the specified space's configured data source.

        Args:
            self (ManualUpload): The ManualUpload object.
            space (SpaceKey): The space to retrieve the document list for.
            configs (dict): A dictionary of configuration options.
            persist_path (str): The path to the directory where the document list for the data source will persist its data.

        Returns:
            list[tuple[str, int, int]]: A list of tuples containing the name, creation time, and size of each document in the specified space's upload directory.
        """
        return self._load_document_list(persist_path, self._DOCUMENT_LIST_FILENAME)

    def _save_document_list(self, persist_path: str, filename: str) -> None:
        path = os.path.join(persist_path, filename)
        with open(path, "w") as f:
            json.dump(
                self._document_list,
                f,
                ensure_ascii=False,
            )

    def _load_document_list(self, persist_path: str, filename: str) -> list[tuple[str, int, int]]:
        path = os.path.join(persist_path, filename)
        with open(path, "r") as f:
            return json.load(f)


class GenericKnowledgeBaseExtractor(BaseTextExtractor):
    """Extract text from a KnowledgeBase documentation site."""

    def extract_text(
        self,
        soup: any,
        page_url: str,
    ) -> str:
        """Extract text from a ReadTheDocs documentation site."""
        content_body = ""
        try:
            p_tags = soup.find_all("p")

            for p in p_tags:
                if p:
                    content_body += f"/n{p.get_text()}"

        except IndexError:
            content_body = None
            log.info("GenericKnowledgeBaseExtractor: No text blocks found on: %s", page_url)

        return content_body

    def link_extract_selector(self) -> any:  # noqa: D102
        return None