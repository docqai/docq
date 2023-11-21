"""Formatters used in the web app."""

from datetime import datetime


def format_timestamp(ts: float) -> str:
    """Format timestamp to human-friendly value."""
    return format_datetime(datetime.fromtimestamp(ts))


def format_datetime(dt: datetime) -> str:
    """Format datetime to human-friendly value."""
    return dt.strftime("%d %b %Y %H:%M")


def format_duration(dt: datetime) -> str:
    """Format time duration to human-friendly value."""
    now = datetime.now().day
    if now == dt.date().day:
        return "Today"
    elif now - dt.date().day == 1:
        return "Yesterday"
    elif now - dt.date().day < 7:
        return "Previous 7 days"
    elif now - dt.date().day < 30:
        return "Previous 30 days"
    else:
        return dt.strftime("%B %Y")


def format_filesize(size: int) -> str:
    """Format filesize to human-friendly sizing string with unit."""
    if size > 1024 * 1024:
        return f"{round(size / 1024 / 1024, 1)} Mb"
    elif size > 1024:
        return f"{round(size / 1024 , 1)} Kb"
    else:
        return f"{size} bytes"


def format_archived(text: str, archived: bool = True) -> str:
    """Format a line of text depending on whether it's archived or not."""
    return f"{'~~' if archived else ''}{text}{'~~' if archived else ''}"
