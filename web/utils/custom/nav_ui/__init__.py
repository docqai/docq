"""Nav UI example."""
import json
import os

import streamlit.components.v1 as components

parent_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(parent_dir, "static", "nav.js")

script = ""
with open(script_path) as f:
    script = f.read()

def my_component(options: list) -> None:
    """SIDE BAR."""
    list_str = json.dumps(options)
    print(f"\x1b[32m{list_str}\x1b[0m")
    components.html(f"<script>{script.replace('{{org-menu-options}}', list_str)}</script>", height=0)

