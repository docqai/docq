"""Header bar."""
from streamlit.components.v1 import html

script = ""
with open("web/st_components/page_header/static/header.js") as f:
    script = f.read()



def header(username: str, avatar_src: str) -> None:
    """Header bar."""
    s = script.replace('{{avatar-src}}', avatar_src)
    j = s.replace('{{username}}', username)
    html(f"<script>{j}</script>",height=0,)
