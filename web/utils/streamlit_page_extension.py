"""Extension of StreamlitPage class to add more functionality.

The property `hidden` is added so our custom navigation can hide pages.
"""

from pathlib import Path
from typing import Callable, Self

from streamlit.navigation.page import StreamlitPage


class StreamlitPageExtension(StreamlitPage):
    """Extension of StreamlitPage class to add more functionality."""

    def __init__(
        self,
        page: str | Path | Callable[[], None],
        *,
        title: str | None = None,
        icon: str | None = None,
        url_path: str | None = None,
        default: bool = False,
        hidden: bool = False,
    ) -> None:
        """Initialize the StreamlitPageExtension class.

        Args:
          page (str | Path | Callable[[], None]): The page to be displayed.
          title (str | None, optional): The title of the page. Defaults to None.
          icon (str | None, optional): The icon of the page. Defaults to None.
          url_path (str | None, optional): The URL path of the page. Defaults to None.
          default (bool, optional): Whether the page is the default page. Defaults to False.
          hidden (bool, optional): Whether the page is hidden in navigation. Defaults to False.
        """
        super().__init__(page=page, title=title, icon=icon, url_path=url_path, default=default)
        self._hidden = hidden

    @property
    def hidden(self) -> bool:
        """If the page is hidden in navigation.

        Returns:
          bool: True If the page is hidden in navigation.
        """
        return self._hidden
