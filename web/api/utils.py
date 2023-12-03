"""Utilities for the API handlers."""
import functools
from typing import Any, Callable

from opentelemetry import trace
from tornado.web import HTTPError, RequestHandler

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("authenticated")
def authenticated(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorate RequestHandler methods with this to require a valid token."""
    @functools.wraps(method)
    def wrapper(self: RequestHandler, *args: Any, **kwargs: Any) -> Any:
        span = trace.get_current_span()
        try:
            auth_header = self.request.headers.get("Authorization")
            if not auth_header:
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(ValueError("Missing Authorization header"))
                raise HTTPError(401, "Missing Authorization header")

            scheme, token = auth_header.split(" ")
            if scheme.lower() != "bearer":
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(ValueError("Authorization scheme must be Bearer"))
                raise HTTPError(401, "Authorization scheme must be Bearer")

            if not validate_token(token):
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(ValueError("Invalid token"))
                raise HTTPError(401, "Invalid token")

            return method(self, *args, **kwargs)
        except ValueError as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            span.record_exception(e)
            raise HTTPError(401, "Invalid Authorization header") from e
    return wrapper

def validate_token(token: str) -> bool:
    """Validate the token. This is just a placeholder, replace with your own validation logic."""
    #TODO: add token validation logic
    return token == "expected_token"