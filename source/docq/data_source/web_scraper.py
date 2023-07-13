"""Data source backed by AWS S3 (bucket)."""

import json
import logging as log
import os
import re
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urljoin

from llama_index import Document
from llama_index.readers.base import BaseReader

from ..config import SpaceDataSourceType
from ..domain import ConfigKey, SpaceKey
from ..support.store import get_index_dir
from .main import DocumentMetadata, SpaceDataSourceFileBased


class WebScraper(SpaceDataSourceFileBased):
    """Data scraped from a website."""

    _DOCUMENT_LIST_FILENAME = "document_list.json"

    def __init__(self) -> None:
        """Initialize the data source.

        Args:
            persist_path (str): The path to the directory where the document list for the data source will persist its data.
        """
        super().__init__(SpaceDataSourceType.WEB_SCRAPER.value, SpaceDataSourceType.WEB_SCRAPER.name)
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
                DocumentMetadata.SPACE_ID.name: space.id_,
                DocumentMetadata.SPACE_TYPE.name: space.type_.name,
            }

        try:
            log.debug("config: %s", configs)
            documents = BeautifulSoupWebReader(website_metadata=lambda_metadata).load_data(
                urls=[configs["website_url"]],
                custom_hostname=configs["extractor_name"],
                include_filter=configs["include_filter"],
            )

            self._document_list = list(
                map(
                    lambda doc: (
                        doc.extra_info[DocumentMetadata.SOURCE_URI.name.lower()],
                        datetime.timestamp(datetime.now().utcnow()),
                        0,
                    ),
                    documents,
                )
            )  # TODO: add size. maybe change to be returned directly from BeautifulSoupWebReader.load_data()

            # path = os.path.join(get_index_dir(space), "documents_metadata.json")
            # path = os.path.join(persist_path, self._DOCUMENT_LIST_FILENAME)
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
        return self._get_document_list(persist_path, self._DOCUMENT_LIST_FILENAME)

    def _save_document_list(self, persist_path: str, filename: str) -> None:
        path = os.path.join(persist_path, filename)
        with open(path, "w") as f:
            json.dump(
                self._document_list,
                f,
                ensure_ascii=False,
            )

    def _get_document_list(self, persist_path: str, filename: str) -> list[tuple[str, int, int]]:
        path = os.path.join(persist_path, filename)
        with open(path, "r") as f:
            return json.load(f)


def _readthedocs_reader(
    soup: Any,
    url: str,
    extra_info: dict = None,
    include_filter: str = None,
) -> List[Document]:
    """Extract text from a ReadTheDocs documentation site."""
    import requests
    from bs4 import BeautifulSoup

    documents = []

    log.debug(">> %s", url)
    links = soup.find_all("a", {"class": "reference internal"})
    rtd_links = []

    for link in links:
        rtd_links.append(link["href"])
    for i in range(len(rtd_links)):  # convert any relative links to fully qualified
        if not rtd_links[i].startswith("http"):
            rtd_links[i] = urljoin(url, rtd_links[i])

    for doc_link in rtd_links:
        log.debug(
            "include filter: %s, ismatch: %s",
            include_filter,
            bool(re.search(include_filter, doc_link)),
        )
        if (not include_filter) or (  # no filter means index everything
            include_filter and re.search(include_filter, doc_link)
        ):
            page_link = requests.get(doc_link, timeout=5)
            soup = BeautifulSoup(page_link.text, "html.parser")
            try:
                text = soup.find(attrs={"role": "main"}).get_text()
                # title = soup.title.get_text()

            except IndexError:
                text = None
                log.info("readthedocs_reader: No text blocks found on: %s", doc_link)

            metadata = {
                "source_website": url,
                "source_uri": doc_link,
                "indexed_on": datetime.timestamp(datetime.now().utcnow()),
            }
            if extra_info is not None:
                metadata.update(extra_info)

            documents.append(Document(text=text, extra_info=metadata))
    return documents


def _generic_reader(
    soup: Any,
    url: str,
    extra_info: dict = None,
    include_filter: str = None,
) -> List[Document]:
    """Extract text from a ReadTheDocs documentation site."""
    import requests
    from bs4 import BeautifulSoup

    documents = []

    log.debug(">> %s", url)
    links = soup.find_all("a")
    rtd_links = []

    for link in links:
        rtd_links.append(link["href"])
    for i in range(len(rtd_links)):  # convert any relative links to fully qualified
        if not rtd_links[i].startswith("http"):
            rtd_links[i] = urljoin(url, rtd_links[i])

    loaded_links = []

    for doc_link in rtd_links:
        log.debug(
            "include filter: %s, ismatch: %s",
            include_filter,
            bool(re.search(include_filter, doc_link)),
        )
        if (doc_link not in loaded_links) and (
            (not include_filter) or (include_filter and re.search(include_filter, doc_link))
        ):  # no filter means index everything
            loaded_links.append(doc_link)  # track URLs we hit already
            page_link = requests.get(doc_link, timeout=5)
            soup = BeautifulSoup(page_link.text, "html.parser")
            try:
                tags = soup.find_all("p")
                p_text = ""
                for p in tags:
                    p_text += f"/n{p.get_text()}"
                    # title = soup.title.get_text()
            except IndexError:
                p_text = None
                log.info("generic_reader: No text blocks (<p> tags) found on: %s", doc_link)

            metadata = {
                "source_website": url,
                "source_uri": doc_link,
                "indexed_on": datetime.timestamp(datetime.now().utcnow()),
            }
            if extra_info is not None:
                metadata.update(extra_info)

            log.debug("generic_reader - uri: %s, extra_infro: %s, text: %s", doc_link, metadata, bool(p_text))
            documents.append(Document(text=p_text, extra_info=metadata))

    return documents


DEFAULT_WEBSITE_EXTRACTOR: Dict[str, Callable[[Any, str], Tuple[str, Dict[str, Any]]]] = {  # noqa: N806
    "default": _generic_reader,
    "readthedocs.io": _readthedocs_reader,
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

        all_documents = []
        for url in urls:
            try:
                page = requests.get(url, timeout=5)
            except Exception:
                raise ValueError(f"One of the inputs is not a valid url: {url}")  # noqa: B904

            hostname = custom_hostname or urlparse(url).hostname or ""

            soup = BeautifulSoup(page.content, "html.parser")

            if hostname in self.website_extractor:
                documents = self.website_extractor[hostname](
                    soup=soup,
                    url=url,
                    extra_info=self.website_metadata(url) if self.website_metadata is not None else {},
                    include_filter=include_filter,
                )
            else:
                documents = self.website_extractor["default"](
                    soup=soup,
                    url=url,
                    extra_info=self.website_metadata(url) if self.website_metadata is not None else {},
                    include_filter=include_filter,
                )

            all_documents = all_documents + documents

        return all_documents
