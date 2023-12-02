"""REST API route handlers.

Route handlers can be split across modules files. 
But you must make sure to import the module at the entry point of the Streamlit app.
For Docq that's the `web/index.py`

See Tornado docs for details on the RequestHandler class:
https://www.tornadoweb.org/en/stable/web.html
"""

from typing import Self

from tornado.web import RequestHandler

from web.utils.streamlit_application import st_app


@st_app.api_route("/api/hello")
class HelloHandler(RequestHandler):
    """Handle /api/hello requests."""

    def get(self: Self) -> None:
        """Handle GET request."""
        self.write({"message": "hello world"})


@st_app.api_route("/api/chat/completion")
class Hello2Handler(RequestHandler):
    """Handle /api/hello2 requests."""

    def post(self: Self) -> None:
        """Handle GET request."""
        self.write({"message": "hello world 2"})
