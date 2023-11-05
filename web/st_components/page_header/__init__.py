"""Header bar."""
import os

from streamlit.components.v1 import html

from ..static_utils import load_file_variables

parent_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(parent_dir, "static", "header.js")
css_path = os.path.join(parent_dir, "static", "header.css")
main_menu_script = os.path.join(parent_dir, "static", "main_menu.js")

# Run this at the start of each page
def _setup_page_script(auth_state: bool) -> None:
    """Setup page script."""
    auth_ = "true" if auth_state else "false"
    html(
        f"""
        <script>
            if (!{auth_}) {{
                const __parent = window.parent.document || window.document;
                const docqHeader = __parent.getElementById("docq-header-container");
                if (docqHeader) {{
                    docqHeader.remove();
                }}
            }}
        </script>
        """,
        height=0
    )


def run_script(auth_state: bool, username: str, avatar_src: str, selected_org: str) -> None:
    """Render the header bar."""
    style = load_file_variables(css_path, {})
    script_args = {
        "username": username,
        "avatar_src": avatar_src,
        "style_doc": style,
        "auth_state": "authenticated" if auth_state else "unauthenticated",
        "selected_org": selected_org,
    }
    html(f"<script>{load_file_variables(script_path, script_args)}</script>", height=0)


def create_menu_items() -> None:
    """Create menu items."""
    html(f"<script>{load_file_variables(main_menu_script, {})}</script>", height=0)
