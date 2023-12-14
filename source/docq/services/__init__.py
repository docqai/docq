"""Docq services."""
from . import credential_utils, google_drive, ms_onedrive, smtp_service

__all__ = [
    "google_drive",
    "smtp_service",
    "ms_onedrive",
    "credential_utils",
]

def _init() -> None:
    """Initialize all default services."""
    google_drive._init()
    ms_onedrive._init()
