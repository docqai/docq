"""Track processed Slack events in memory to help detect duplicates."""

from datetime import datetime, timezone
from typing import Optional, Self


class Tracker:
    """Class to track anything across multiple sessions outside Streamlit.

    Create an instance globally.
    """

    shared_dict = {}

    def __init__(self: Self, ttl_sec: Optional[int] = 600) -> None:
        """Initialize the tracker."""
        self.shared_dict = {}

    def add_key(self: Self, unique_key: str) -> bool:
        """Add unique key if it doesn't exist.

        Returns:
            bool: True if the key was added, False if it already exists.
        """
        added = False
        if unique_key not in self.shared_dict:
            self.shared_dict[unique_key] = datetime.now(timezone.utc)
            added = True

        return added

    def remove_key(self: Self, unique_key: str) -> bool:
        """Remove an event from the tracker.

        Returns:
            bool: True if the key was removed, False if it doesn't exist.
        """
        removed = False
        if unique_key in self.shared_dict:
            del self.shared_dict[unique_key]
            removed = True
        return removed


class SlackEventTracker(Tracker):
    """Class to track processed Slack events."""

    def add_event(self: Self, event_id: str, channel_id: str) -> bool:
        """Add an event to the tracker.

        Returns:
            bool: True if the event was added, False if it already exists.
        """
        return super().add_key(self._get_unique_key(event_id, channel_id))

    def remove_event(self: Self, event_id: str, channel_id: str) -> bool:
        """Remove an event from the tracker.

        Returns:
            bool: True if the event was removed, False if it doesn't exist.
        """
        return super().remove_key(self._get_unique_key(event_id, channel_id))

    @staticmethod
    def _get_unique_key(event_id: str, channel_id: str) -> str:
        """Get a unique key for an event."""
        return f"{channel_id}_{event_id}"
