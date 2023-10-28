"""Prompts the user to authorize access to G-Drive."""

from utils.layout import auth_required, authorize_gdrive_ui

auth_required()

authorize_gdrive_ui()
