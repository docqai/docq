"""REST API route handlers.

Route handlers can be split across modules files. 
But you must make sure to import the module at the entry point of the Streamlit app.
For Docq that's the `web/index.py`

See Tornado docs for details on the RequestHandler class:
https://www.tornadoweb.org/en/stable/web.html


Naming convention:
module name: route replace `/` with `_`
class name: route replace capitalise route segments remove `/` and `_`

Example:
- `/api/hello` -> `hello_handler`


"""

from typing import Self

from tornado.web import RequestHandler

from web.utils.streamlit_application import st_app

# for now we'll manually add imports. TODO: convert to walk the directory and dynamically import using importlib
from . import chat_completion_handler  # noqa: F401 DO NOT REMOVE


@st_app.api_route("/api/hello")
class HelloHandler(RequestHandler):
    """Handle /api/hello requests."""

    def get(self: Self) -> None:
        """Handle GET request."""
        self.write({"message": "hello world"})

