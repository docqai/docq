"""Tests for the ReadTheDocsTextExtractor class."""
import unittest

from bs4 import BeautifulSoup
from docq.data_source.web_scraper import ReadTheDocsTextExtractor


class TestReadTheDocsTextExtractor(unittest.TestCase):  # noqa: D101
    def setUp(self) -> None:
        """Set up the test by creating a new instance of ReadTheDocsTextExtractor."""
        self.extractor: ReadTheDocsTextExtractor = ReadTheDocsTextExtractor()

    def test_extract_text(self) -> None:
        """Test that extract_text returns the expected text."""
        soup = BeautifulSoup("<div role='main'>Hello, world!</div>", "html.parser")
        text: str = self.extractor.extract_text(soup, "http://example.com")
        assert text == "Hello, world!"

    def test_extract_text_no_text_blocks(self) -> None:
        """Test that extract_text returns None when no text blocks are found."""
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        text = self.extractor.extract_text(soup, "http://example.com")
        assert text is None

    def test_link_extract_selector(self) -> None:
        """Test that link_extract_selector returns the expected CSS class name.

        This test ensures that the link_extract_selector method of the ReadTheDocsTextExtractor class
        returns the expected CSS class name. The expected CSS class name is "reference internal".
        """
        css_class = self.extractor.link_extract_selector()
        assert css_class == "reference internal"
