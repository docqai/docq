"""Llama Index callback handler for OpenTelemetry tracing."""

import inspect
import logging
from typing import Any, Dict, List, Optional, Self, Tuple

from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan

import llama_index.core
from llama_index.core.callbacks.base_handler import BaseCallbackHandler
from llama_index.core.callbacks.schema import CBEventType, EventPayload

logger = logging.getLogger(__name__)


class OtelCallbackHandler(BaseCallbackHandler):
    """Base callback handler that can be used to track event starts and ends."""

    _spans: dict[str, Any] = {}  # track Otel spans so they can be ended on the end events.

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
        # module_name, function_name = get_caller_function_and_module()
        self._tracer = tracer_provider.get_tracer(
            instrumenting_module_name="docq.llama_index_otel_callbackhandler",
            instrumenting_library_version=llama_index.core.__version__,
        )

        super().__init__(
            event_starts_to_ignore=start_ignore,
            event_ends_to_ignore=end_ignore,
        )

    def on_event_start(
        self: Self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        """Run when an event starts and return id of event."""
        try:
            # logging.debug("Starting event event_id: %s, event_type: %s, payload: %s", event_id, event_type, payload)
            parent_span = self._spans[parent_id] if parent_id in self._spans else trace.get_current_span()
            ctx = trace.set_span_in_context(NonRecordingSpan(parent_span.get_span_context()))
            span = self._tracer.start_span(
                name=event_type.name, context=ctx, attributes=self._serialize_payload(payload)
            )
            span.add_event(
                name="callback_handler.on_event_start",
                attributes={
                    "cbevent.event_id": event_id,
                    "cbevent.parent_id": parent_id,
                    "cbevent.event_type": event_type,
                },
            )
            self._spans[event_id] = span

        except Exception as e:
            logger.error("tracer threw an error: %s", e)

        return event_id

    def on_event_end(
        self: Self,
        event_type: CBEventType,
        payload: Optional[Dict[str, Any]] = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        """Run when an event ends."""
        # logger.debug("Ending event - event_id: '%s', event_type: '%s', event_payload: '%s'", event_id, event_type, payload)
        if event_id in self._spans:
            span = self._spans.pop(event_id)
            span.set_attributes(self._serialize_payload(payload))
            span.add_event(
                name="callback_handler.on_event_end",
                attributes={"cbevent.event_id": event_id, "cbevent.event_type": event_type},
            )
            span.end()

    def start_trace(self: Self, trace_id: Optional[str] = None) -> None:
        """Run when an overall trace is launched."""
        if trace_id:
            # logger.debug("Starting trace - trace_id: '%s'", trace_id)
            current_span = trace.get_current_span()
            ctx = trace.set_span_in_context(NonRecordingSpan(current_span.get_span_context()))
            span = self._tracer.start_span(name=trace_id, context=ctx)
            span.add_event(name="callback_handler.start_trace", attributes={"cbevent.trace_id": trace_id})
            self._spans[trace_id] = span

    def end_trace(
        self: Self,
        trace_id: Optional[str] = None,
        trace_map: Optional[Dict[str, List[str]]] = None,
    ) -> None:
        """Run when an overall trace is exited."""
        # logger.debug("Ending trace - trace_id: '%s'", trace_id)
        # logger.debug("Ending trace - trace_map: '%s'", trace_map)
        if trace_id and trace_id in self._spans:
            span = self._spans.pop(trace_id)
            span.add_event(name="callback_handler.end_trace", attributes={"cbevent.trace_id": trace_id})
            span.end()

    @staticmethod
    def _serialize_payload(payload: Dict[str, Any] | None) -> Dict[str, str]:
        """Serialize payload."""
        _result: Dict[str, str] = {}
        try:
            if payload:
                if EventPayload.SERIALIZED in payload:
                    _result = payload[EventPayload.SERIALIZED]
                else:
                    _result = {k: str(v) for k, v in payload.items()}
        except Exception as e:
            _result = {EventPayload.EXCEPTION: "error message: " + str(e)}
            logger.error("tracer threw an error: %s", e)

        return _result

    @staticmethod
    def get_caller_function_and_module() -> Tuple[str, str]:
        """Get the caller function and module."""
        function_name, module_name = "", ""
        # Get the frame of the caller
        frame = inspect.currentframe()
        if frame is not None:
            _frame = frame.f_back
            if _frame is not None:
                # Get the name of the function of the caller
                frame_info = inspect.getframeinfo(frame)
                function_name = frame_info.function

        # Get the name of the module of the caller
        module = inspect.getmodule(frame)
        if module is not None:
            module_name = module.__name__

        return function_name, module_name
