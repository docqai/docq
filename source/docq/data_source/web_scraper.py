"""Data source for scrapping a website."""

import json
import logging as log
import os
import re
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from llama_index import Document
from llama_index.readers.base import BaseReader

from ..domain import ConfigKey, SpaceKey
from .main import DocumentMetadata, SpaceDataSourceWebBased


class WebScraper(SpaceDataSourceWebBased):
    """Data scraped from a website."""

    _DOCUMENT_LIST_FILENAME = "document_list.json"

    def __init__(self) -> None:
        """Initialize the data source."""
        super().__init__("Web Scraper", "WEB_SCRAPER")
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
        ]

    def load(self, space: SpaceKey, configs: dict, persist_path: str) -> List[Document]:
        """Extract text from web pages on a website and load each page as a Document."""

        def lambda_metadata(x: str) -> dict:
            return {
                DocumentMetadata.SPACE_ID.value: space.id_,
                DocumentMetadata.SPACE_TYPE.value: space.type_.name,
                DocumentMetadata.DATA_SOURCE_TYPE.value: self.get_type(),
            }

        try:
            log.debug("config: %s", configs)

            bs_web_reader = BeautifulSoupWebReader(website_metadata=lambda_metadata)
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


class BaseTextExtractor(ABC):
    """Abstract base class for webpage text extractors."""

    def __init__(
        self,
        title_css_selector: str = None,
        subtitle_css_selector: str = None,
    ) -> None:
        """Initialize the text extractor."""
        self._title_css_selector = title_css_selector
        self._subtitle_css_selector = subtitle_css_selector

    @abstractmethod
    def extract_text(
        self,
        soup: any,
        page_url: str,
    ) -> str:
        """Extract text from a web page."""
        pass

    @abstractmethod
    def link_extract_selector() -> any:
        """Criteria filter specific <a> tags to extract links from. To extract all links, return None."""
        pass

    def extract_title(self, soup: any, css_selector: str = None) -> str:  # noqa: D102
        """Extract the title from a web page. Defaults to the <h1> tag.

        Args:
            soup (any): The BeautifulSoup object representing the web page.
            css_selector (str, optional): The CSS selector to use to find the title. BeautifulSoup style. Defaults to None.
        """
        self._title_css_selector = css_selector if css_selector else self._title_css_selector

        title_element = soup.find(class_=self._title_css_selector) if self._title_css_selector else soup.find("h1")

        return title_element.get_text() if title_element else ""

    def extract_subtitle(self, soup: any, css_selector: str = None) -> str:
        """Extract the subtitle from a web page. Defaults to the <h2> tag.

        Args:
            soup (any): The BeautifulSoup object representing the web page.
            css_selector (str, optional): The CSS selector to use to find the subtitle. BeautifulSoup style. Defaults to None.

        Returns:
            str: The subtitle text.
        """
        self._subtitle_css_selector = css_selector if css_selector else self._subtitle_css_selector

        subtitle_element = (
            soup.find(class_=self._subtitle_css_selector) if self._subtitle_css_selector else soup.find("h2")
        )

        return subtitle_element.get_text() if subtitle_element else ""

    def extract_links(self, soup: any, website_url: str, extract_url: str, include_filter: str = None) -> List[str]:
        """Extract a unique list of links from a website."""
        log.debug("Extract links from root URL: %s", extract_url)

        links = (
            soup.find_all("a", class_=self.link_extract_selector())
            if self.link_extract_selector() is not None
            else soup.find_all("a")
        )
        log.debug("Total links on page: %s", len(links))
        rtd_links = []

        for link in links:
            href = link.get("href")
            log.debug("link: %s, href: %s", link, href)
            ismatch = False
            if (
                (href is not None)
                and (href not in rtd_links)
                and ((not include_filter) or (include_filter and re.search(include_filter, href)))
            ):  # apply filter and ignore duplicate links
                # no filter means index everything
                ismatch = True

                if not href.startswith("http"):
                    href = urljoin(website_url, href)

                rtd_links.append(href)

            log.debug("include filter: %s, ismatch: %s", include_filter, ismatch)

        log.debug("Total links for extraction: %s", len(rtd_links))
        return rtd_links


class ReadTheDocsTextExtractor(BaseTextExtractor):
    """Extract text from a ReadTheDocs documentation site."""

    def extract_text(
        self,
        soup: any,
        page_url: str,
    ) -> str:
        """Extract text from a ReadTheDocs documentation site."""
        try:
            node = soup.find(attrs={"role": "main"})
            text = node.get_text() if node else None

        except IndexError:
            text = None
            log.info("readthedocs_reader: No text blocks found on: %s", page_url)

        return text

    def link_extract_selector(self) -> any:  # noqa: D102
        """Return CSS class names to filter <a> tags. To extract all links, return None."""
        return "reference internal"


class GenericTextExtractor(BaseTextExtractor):
    """Extract text from any website on a best efforts basis, naive implementaion. Not recursive."""

    def extract_text(
        self,
        soup: any,
        page_url: str,
    ) -> str:
        """Extract text from any website on a best efforts basis, naive implementaion. Not recursive."""
        try:
            tags = soup.find_all("p")
            page_text = ""
            for p in tags:
                page_text += f"/n{p.get_text()}"
        except IndexError:
            page_text = None
            log.info("generic_reader: No text blocks (<p> tags) found on: %s", page_url)

        return page_text

    def link_extract_selector(self) -> any:  # noqa: D102
        return None


DEFAULT_WEBSITE_EXTRACTOR: Dict[str, Callable[[Any, str], Tuple[str, Dict[str, Any]]]] = {  # noqa: N806
    "default": GenericTextExtractor(),
    "readthedocs.io": ReadTheDocsTextExtractor(),
}


class BeautifulSoupWebReader(BaseReader):
    """BeautifulSoup web page reader.

    Reads pages from the web.
    Requires the `bs4` and `urllib` packages.

    Args:
        website_extractor (Optional[Dict[str, Callable]]): A mapping of website
            hostname (e.g. google.com) to a function that specifies how to
            extract text from the BeautifulSoup obj. See DEFAULT_WEBSITE_EXTRACTOR.
    """

    def __init__(
        self,
        website_extractor: Optional[Dict[str, Callable]] = None,
        website_metadata: Optional[Callable[[str], Dict]] = None,
    ) -> None:
        """Initialize with parameters."""
        self.website_extractor = website_extractor or DEFAULT_WEBSITE_EXTRACTOR
        self.website_metadata = website_metadata
        self._document_list: list[tuple[str, int, int]] = []

    def load_data(
        self,
        urls: List[str],
        custom_hostname: Optional[str] = None,
        include_filter: Optional[str] = None,
    ) -> List[Document]:
        """Load data from the urls.

        Args:
            urls (List[str]): List of URLs to scrape.
            custom_hostname (Optional[str]): Force a certain hostname in the case
                a website is displayed under custom URLs (e.g. Substack blogs)
            include_filter (Optional[str]): Only scrape pages that match this regex.
            exclude_filter (Optional[str]): Do not scrape pages that match this regex.

        Returns:
            List[Document]: List of documents.

        """
        from urllib.parse import urlparse

        import requests
        from bs4 import BeautifulSoup

        all_documents: List[Document] = []
        urls = urls[0].split(",")
        log.debug("Number of root URLs supplied: %s", len(urls))
        log.debug("root URLs supplied: %s", urls)

        for url in urls:
            log.debug("Now processing root URL: %s", url)
            hostname = custom_hostname or urlparse(url).hostname or ""

            try:
                page = requests.get(url, timeout=5)
            except Exception as e:
                raise ValueError(f"One of the inputs is not a valid url: {url}", e)  # noqa: B904

            soup = BeautifulSoup(page.content, "html.parser")

            if hostname in self.website_extractor:
                extractor: BaseTextExtractor = self.website_extractor[hostname]
            else:
                extractor: BaseTextExtractor = self.website_extractor["default"]

            page_links = extractor.extract_links(soup, url, url, include_filter=include_filter)

            for page_link in page_links:
                try:
                    page_reponse = requests.get(page_link, timeout=5)
                    soup = BeautifulSoup(
                        page_reponse.text, "html.parser"
                    )  # TODO: not sure why the original code used reponse.text here and response.content above. dig in later.

                    page_text = extractor.extract_text(
                        soup=soup,
                        page_url=page_link,
                    )

                    page_title = extractor.extract_title(soup=soup)
                    page_subtitle = extractor.extract_subtitle(soup=soup)

                    metadata = {
                        "source_website": url,
                        "source_uri": page_link,
                        "indexed_on": datetime.timestamp(datetime.now().utcnow()),
                        "page_title": page_title,
                        "page_subtitle": page_subtitle,
                    }

                    if self.website_metadata is not None:
                        metadata.update(self.website_metadata(url))

                    all_documents.append(Document(text=page_text, extra_info=metadata))

                    size_in_bytes = sys.getsizeof(page_text)

                    size_in_megabytes = size_in_bytes if size_in_bytes > 0 else 0

                    self._document_list.append(
                        (page_link, datetime.timestamp(datetime.now().utcnow()), size_in_megabytes)
                    )
                except Exception as e:
                    log.error("Error requesting web page, skipped: %s, Error: %s", page_link, e)
                    continue

        return all_documents

    def get_document_list(self) -> List[tuple[str, int, int]]:
        """Return a list of documents. Can be used for tracking state overtime by implementing persistence and displaying document lists to users."""
        return self._document_list
