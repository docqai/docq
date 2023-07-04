"""Formatters used in the web app."""

from datetime import datetime


def format_datetime(dt: datetime) -> str:
    """Format datetime to human-friendly value."""
    return dt.strftime("%d %b %Y %H:%M")


def format_filesize(size: int) -> str:
    """Format filesize to human-friendly Mb sizing."""
    return f"{round(size / 1024 / 1024, 1)} Mb"
