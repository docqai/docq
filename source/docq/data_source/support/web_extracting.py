"""Web page text extraction."""

import logging as log
import re
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from llama_index import Document
from llama_index.readers.base import BaseReader


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
    """Extract text from any website on a best efforts basis, naive implementation. Not recursive."""

    def extract_text(
        self,
        soup: any,
        page_url: str,
    ) -> str:
        """Extract text from any website on a best efforts basis, naive implementation. Not recursive."""
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


class BeautifulSoupWebReader(BaseReader):
    """BeautifulSoup web page reader.

    Reads pages from the web.
    Requires the `bs4` and `urllib` packages.

    Args:
        website_extractor (Optional[Dict[str, Callable]]): A mapping of website
            hostname (e.g. google.com) to a function that specifies how to
            extract text from the BeautifulSoup.
    """

    def __init__(
        self,
        website_extractors: Dict[str, BaseTextExtractor] = None,
        website_metadata: Optional[Callable[[str], Dict]] = None,
    ) -> None:
        """Initialize with parameters."""
        self.website_extractors = website_extractors
        self.website_metadata = website_metadata
        self._document_list: list[tuple[str, int, int]] = []

    def load_data(
        self,
        urls: List[str],
        include_filter: str = None,
    ) -> List[Document]:
        """Load data from the urls.

        Args:
            urls (List[str]): List of URLs to scrape.
            include_filter (Optional[str]): Only scrape pages that match this regex.

        Returns:
            List[Document]: List of documents.

        """
        all_documents: List[Document] = []
        urls = urls[0].split(",")
        log.debug("Number of root URLs supplied: %s", len(urls))
        log.debug("root URLs supplied: %s", urls)

        for url in urls:
            log.debug("Now processing root URL: %s", url)
            hostname = urlparse(url).hostname or "default"

            try:
                page = requests.get(url, timeout=5)
            except Exception as e:
                raise ValueError(f"One of the inputs is not a valid url: {url}", e)  # noqa: B904

            soup = BeautifulSoup(page.content, "html.parser")

            if hostname in self.website_extractors:
                extractor: BaseTextExtractor = self.website_extractors[hostname]
            else:
                extractor: BaseTextExtractor = self.website_extractors["default"]

            page_links = extractor.extract_links(soup, url, url, include_filter=include_filter)

            for page_link in page_links:
                try:
                    page_response = requests.get(page_link, timeout=5)
                    soup = BeautifulSoup(
                        page_response.text, "html.parser"
                    )  # TODO: not sure why the original code used response.text here and response.content above. dig in later.

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

                    all_documents.append(Document(text=page_text, metadata=metadata))

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
