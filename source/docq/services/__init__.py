"""Docq services."""
from . import google_drive, smtp_service

__all__ = [
    "google_drive",
    "smtp_service"
]

def _init() -> None:
    """Initialize all default services."""
    google_drive._init()
