"""Web page text extraction."""

import logging as log
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Self
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document
from opentelemetry import trace

from ...domain import DocumentListItem, SourcePageType

tracer = trace.get_tracer(__name__)


class BaseTextExtractor(ABC):
    """Abstract base class for webpage text extractors."""

    def __init__(
        self: Self,
        title_css_selector: Optional[str] = None,
        subtitle_css_selector: Optional[str] = None,
    ) -> None:
        """Initialize the text extractor."""
        self._title_css_selector = title_css_selector
        self._subtitle_css_selector = subtitle_css_selector

    @abstractmethod
    @tracer.start_as_current_span(name="extract_text")
    def extract_text(
        self: Self,
        soup: Any,
        page_url: str,
    ) -> str:
        """Extract text from a web page."""
        pass

    @abstractmethod
    @tracer.start_as_current_span(name="link_extract_selector")
    def link_extract_selector() -> Any:
        """Criteria filter specific <a> tags to extract links from. To extract all links, return None."""
        pass

    @tracer.start_as_current_span(name="extract_title")
    def extract_title(self: Self, soup: Any, css_selector: Optional[str] = None) -> str:  # noqa: D102
        """Extract the title from a web page. Defaults to the <h1> tag.

        Args:
            soup (Any): The BeautifulSoup object representing the web page.
            css_selector (str, optional): The CSS selector to use to find the title. BeautifulSoup style. Defaults to None.
        """
        self._title_css_selector = css_selector if css_selector else self._title_css_selector

        if self._title_css_selector:
            title_element = soup.find(class_=self._title_css_selector)
        elif soup.find("h1"):
            title_element = soup.find("h1")
        else:
            title_element = soup.find("title")

        return title_element.get_text() if title_element else "web page"

    @tracer.start_as_current_span(name="extract_subtitle")
    def extract_subtitle(self: Self, soup: Any, css_selector: Optional[str] = None) -> str:
        """Extract the subtitle from a web page. Defaults to the <h2> tag.

        Args:
            soup (Any): The BeautifulSoup object representing the web page.
            css_selector (str, optional): The CSS selector to use to find the subtitle. BeautifulSoup style. Defaults to None.

        Returns:
            str: The subtitle text.
        """
        self._subtitle_css_selector = css_selector if css_selector else self._subtitle_css_selector

        subtitle_element = (
            soup.find(class_=self._subtitle_css_selector) if self._subtitle_css_selector else soup.find("h2")
        )

        return subtitle_element.get_text() if subtitle_element else ""

    @tracer.start_as_current_span(name="extract_links")
    def extract_links(
        self: Self, soup: Any, website_url: str, extract_url: str, include_filter: Optional[str] = None
    ) -> List[str]:
        """Extract a unique list of links from a website."""
        span = trace.get_current_span()
        log.debug("Extract links from root URL: %s", extract_url)
        span.set_attributes(
            {
                "extract_url": extract_url,
                "website_url": website_url,
                "include_filter": str(include_filter),
                "link_extract_selector": self.link_extract_selector(),
            }
        )
        links = (
            soup.find_all("a", class_=self.link_extract_selector())
            if self.link_extract_selector() is not None
            else soup.find_all("a")
        )
        span.set_attribute("total_links_count", len(links).__str__())
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

            log.debug("include filter: %s, ismatc h: %s", include_filter, ismatch)
            span.add_event("link_match", {"link": href, "ismatch": ismatch})

        log.debug("Total links for extraction: %s", len(rtd_links))
        span.set_attribute("links_for_extraction_count", len(rtd_links).__str__())
        return rtd_links


class ReadTheDocsTextExtractor(BaseTextExtractor):
    """Extract text from a ReadTheDocs documentation site."""

    def extract_text(
        self: Self,
        soup: Any,
        page_url: str,
    ) -> Any | None:
        """Extract text from a ReadTheDocs documentation site."""
        try:
            node = soup.find(attrs={"role": "main"})
            text = node.get_text() if node else None

        except IndexError:
            text = None
            log.info("readthedocs_reader: No text blocks found on: %s", page_url)

        return text

    def link_extract_selector(self: Self) -> Any:  # noqa: D102
        """Return CSS class names to filter <a> tags. To extract all links, return None."""
        return "reference internal"


class GenericTextExtractor(BaseTextExtractor):
    """Extract text from Any website on a best efforts basis, naive implementation. Not recursive."""

    def extract_text(
        self: Self,
        soup: Any,
        page_url: str,
    ) -> str | None:
        """Extract text from Any website on a best efforts basis, naive implementation. Not recursive."""
        span = trace.get_current_span()
        try:
            tags = soup.find_all("p")
            span.set_attribute("p_tags_count", len(tags).__str__())
            page_text = ""
            for p in tags:
                page_text += f"/n{p.get_text()}"
        except IndexError:
            page_text = None
            span.set_attribute("p_tags_count", "0")
            log.info("generic_reader: No text blocks (<p> tags) found on: %s", page_url)

        return page_text

    def link_extract_selector(self: Self) -> Any:
        """Return CSS class names to filter <a> tags. To extract all links, return None."""
        return None


class GenericKnowledgeBaseExtractor(BaseTextExtractor):
    """Extract text from a KnowledgeBase documentation site."""

    def extract_text(
        self: Self,
        soup: Any,
        page_url: str,
    ) -> str | None:
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

    def link_extract_selector(self: Self) -> Any:  # noqa: D102
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
        self: Self,
        website_extractors: Dict[str, BaseTextExtractor],
        website_metadata: Optional[Callable[[str], Dict]] = None,
    ) -> None:
        """Initialize with parameters."""
        self.website_extractors = website_extractors
        self.website_metadata = website_metadata
        self._document_list: List[DocumentListItem] = []

    @tracer.start_as_current_span(name="load_data")
    def load_data(
        self: Self,
        urls: List[str],
        include_filter: Optional[str] = None,
        source_page_type: Optional[SourcePageType] = SourcePageType.index_page,
    ) -> List[Document]:
        """Load data from the urls.

        Args:
            urls (List[str]): List of URLs to scrape.
            include_filter (Optional[str]): Only scrape pages that match this regex.

        Returns:
            List[Document]: List of documents.

        """
        span = trace.get_current_span()
        all_documents: List[Document] = []
        page_links: List[str] = []

        if not urls or len(urls) == 0:
            raise ValueError("No URLs supplied.")

        hostname = urlparse(urls[0]).hostname or "default"
        if hostname in self.website_extractors:
            extractor: BaseTextExtractor = self.website_extractors[hostname]
        else:
            extractor: BaseTextExtractor = self.website_extractors["default"]

        span.set_attribute("source_page_type", source_page_type.__str__())

        # page_links = urls  # default case expect page urls to extract content from directly
        print("source page type : ", source_page_type)

        if source_page_type == SourcePageType.index_page:
            # the provided URLs are index pages, extract links from them first
            log.debug("Number of index page URLs supplied: %s", len(urls))
            for url in urls:
                lnk = self._extract_links(url, extractor, include_filter)
                page_links.extend(lnk)
                span.add_event("extracted_links_from_index_page", {"url": url, "links_count": len(lnk)})
        elif source_page_type == SourcePageType.page_list:
            page_links = urls
            print("page list - links : ", page_links)
        else:
            raise ValueError(f"Invalid source page type: {source_page_type}")

        span.set_attribute("page_links_count", len(page_links).__str__())
        print("page links : ", page_links)

        for page_link in page_links:
            try:
                page_response = requests.get(page_link, timeout=5)
                span.add_event("url_requested", {"page_link": page_link, "response_bytes": len(page_response.content)})
                soup = BeautifulSoup(
                    page_response.text, "html.parser"
                )  # TODO: not sure why the original code used response.text here and response.content above. dig in later.

                page_text = extractor.extract_text(
                    soup=soup,
                    page_url=page_link,
                )

                page_title = extractor.extract_title(soup=soup)
                page_subtitle = extractor.extract_subtitle(soup=soup)
                indexed_on = datetime.timestamp(datetime.now().utcnow())
                metadata = {
                    "source_website": urlparse(page_link).hostname,
                    "source_uri": page_link,
                    "indexed_on": indexed_on,
                    "page_title": page_title,
                    "page_subtitle": page_subtitle,
                }

                if self.website_metadata is not None:
                    metadata.update(self.website_metadata(page_link))

                all_documents.append(Document(text=page_text, extra_info=metadata))

                self._document_list.append(DocumentListItem.create_instance(page_link, page_text, int(indexed_on)))

            except Exception as e:
                span.record_exception(e)
                span.set_status(
                    trace.Status(trace.StatusCode.ERROR, f"Error requesting web page, skipped : {page_link}")
                )
                log.exception("Error requesting web page, skipped: %s, Error: %s", page_link, e)
                continue

        return all_documents

    def get_document_list(self: Self) -> List[DocumentListItem]:
        """Return a list of documents. Can be used for tracking state overtime by implementing persistence and displaying document lists to users."""
        return self._document_list

    @staticmethod
    @tracer.start_as_current_span(name="extract_links")
    def _extract_links(url: str, extractor: BaseTextExtractor, include_filter: Optional[str] = None) -> List[str]:
        span = trace.get_current_span()
        log.debug("Now processing root URL: %s", url)
        span.add_event("start_processing_url", {"url": url})

        try:
            page = requests.get(url, timeout=5)
            span.add_event("url_requested", {"url": url, "response_bytes": len(page.content)})
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, f"One of the inputs is not a valid url: {url}"))
            raise ValueError(f"One of the inputs is not a valid url: {url}", e)  # noqa: B904

        soup = BeautifulSoup(page.content, "html.parser")

        # print("page content: ", page.content)

        # print("page text: ", page.text)

        page_links = extractor.extract_links(soup, url, url, include_filter=include_filter)
        return page_links
