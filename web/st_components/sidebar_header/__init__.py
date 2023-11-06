"""Nav UI example."""
import os
from typing import Optional

import streamlit.components.v1 as components

from ..static_utils import load_file_variables

parent_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(parent_dir, "static", "sidebar.js")
css_path = os.path.join(parent_dir, "static", "sidebar.css")


def _get_script(logo_url: Optional[str] = None) -> str:
    """Get the script."""
    style = load_file_variables(css_path, {})
    return load_file_variables(script_path, {
        "logo_url": logo_url,
        "style_doc": style,
    })





def run_script(logo_url: Optional[str] = None) -> None:
    """Run the script."""
    components.html(f"""
        // ST-SIDEBAR-SCRIPT-CONTAINER
        <script>{_get_script(logo_url)}</script>
        """,
        height=0
    )
