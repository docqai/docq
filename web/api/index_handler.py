"""REST API route handlers.

Route handlers can be split across modules files.
Make sure to import the module at the entry point of the Streamlit app.
For Docq that's the `web/index.py`

See Tornado docs for details on the RequestHandler class:
https://www.tornadoweb.org/en/stable/web.html


Naming convention:
module name: route replace `/` with `_`. Example:  `/api/hello/world` -> `hello_world_handler`
class name: route replace capitalise route segments remove `/` and `_`. Example: `/api/hello/world` -> `HelloWorldHandler`
"""

# for now we'll manually add imports. TODO: convert to walk the directory and dynamically import using importlib
from . import (
    chat_completion_handler,  # noqa: F401 DO NOT REMOVE
    file_upload_handler,  # noqa: F401 DO NOT REMOVE
    hello_handler,  # noqa: F401 DO NOT REMOVE
    history_handler,  # noqa: F401 DO NOT REMOVE
    rag_completion_handler,  # noqa: F401 DO NOT REMOVE
    space_handler,  # noqa: F401 DO NOT REMOVE
    thread_handler,  # noqa: F401 DO NOT REMOVE
    token_handler,  # noqa: F401 DO NOT REMOVE
    top_questions_handler,  # noqa: F401 DO NOT REMOVE
)
