"""Signup page for the web app. Supports `email` and `name` as query string params."""


from utils.layout import production_layout, public_access, signup_ui

public_access()
production_layout()

signup_ui()
