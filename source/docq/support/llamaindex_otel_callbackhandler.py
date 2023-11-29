import logging
import uuid
from typing import Any, Dict, List, Optional, Self

import llama_index
from llama_index.callbacks.base_handler import BaseCallbackHandler
from llama_index.callbacks.schema import BASE_TRACE_EVENT, CBEventType
from opentelemetry import trace


class OtelCallbackHandler(BaseCallbackHandler):
    """Base callback handler that can be used to track event starts and ends."""
    _spans: dict[str, Any] = {}
    def __init__(
        self: Self,
        tracer_provider: trace.TracerProvider,
        event_starts_to_ignore: Optional[List[CBEventType]] = None,
        event_ends_to_ignore: Optional[List[CBEventType]] = None,
    ) -> None:
        """Initialize the base callback handler."""
        start_ignore = event_starts_to_ignore or []
        end_ignore = event_ends_to_ignore or []

        self.event_starts_to_ignore = tuple(start_ignore)

        self.event_ends_to_ignore = tuple(end_ignore)

        self._tracer = tracer_provider.get_tracer(instrumenting_module_name="llama_index", instrumenting_library_version=llama_index.__version__)
        logging.debug("OtelCallbackHandler initialized")

    def on_event_start(
        self:Self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Run when an event starts and return id of event."""
        #trace.get_current_span().add_event(name=f"{event_type.value}_started", attributes=payload)
        #logging.debug("Starting event %s, %s", event_type, event_id)
        
        self._spans[event_id] = self._tracer.start_span(name=event_type.value, attributes=payload)

        return event_id

    def on_event_end(
        self: Self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Run when an event ends."""
        #trace.get_current_span().add_event(name=f"{event_type.value}_ended", attributes=payload)
        self._spans[event_id].add_attributes(payload)
        self._spans[event_id].end()

    def start_trace(self: Self, trace_id: Optional[str] = None) -> None:
        """Run when an overall trace is launched."""
        trace_id = trace_id or str(uuid.uuid4())
        with self._tracer.start_as_current_span(name=trace_id):
            pass
        logging.debug("Starting trace %s", trace_id)

    def end_trace(
        self: Self,
        trace_id: Optional[str] = None,
        trace_map: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Run when an overall trace is exited."""
        trace.get_current_span().end()
        logging.debug("Ending trace %s", trace_id)
