"""Signup page for the web app. Supports `email` and `name` as query string params."""


from utils.layout import (
    production_layout,
    public_access,
    render_page_title_and_favicon,
    signup_ui,
)

render_page_title_and_favicon()
public_access()
production_layout()

signup_ui()
