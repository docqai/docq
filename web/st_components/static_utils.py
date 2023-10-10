"""Utility functions for static files."""
from streamlit.source_util import get_pages

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except ImportError:
    from streamlit.scriptrunner.script_run_context import (
        get_script_run_ctx,
    )

import os
import sys


def load_file_variables(file_path: str, vars_: dict = None) -> str:
    """Load file variables."""
    with open(file_path) as f:
        file_str = f.read()
        if vars_:
            for key, value in vars_.items():
                if value is not None:
                    file_str = file_str.replace('{{' + key + '}}', value)
        return file_str


def get_current_page_info() -> str:
    """Get the current page name."""
    main_script_path = os.path.abspath(sys.argv[0])
    pages = get_pages("")
    ctx = get_script_run_ctx()
    if ctx is not None:
        return pages.get(
            ctx.page_script_hash,
            (p for p in pages.values() if p["relative_page_hash"] == ctx.page_script_hash)
        )
    return None
