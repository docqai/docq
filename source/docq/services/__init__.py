"""Docq services."""
from . import google_drive, smtp_service

__all__ = [
    "google_drive",
    "smtp_service"
]

google_drive._init()
