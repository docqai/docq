"""Utilities for the API handlers."""
import functools
import os
import re
from typing import Any, Callable, Iterable, Mapping

from opentelemetry import trace
from pydantic import BaseModel
from tornado.web import HTTPError, RequestHandler

from ...source.docq.config import ENV_VAR_DOCQ_API_SECRET

tracer = trace.get_tracer(__name__)

UNDERSCORE_RE = re.compile(r"(?<=[^\-_])[\-_]+[^\-_]")

def _process_keys(str_or_iter: str | Iterable, fn) -> str | Iterable:
    """Recursively process keys in a string, dict, or list of dicts."""
    if isinstance(str_or_iter, list):
        return [_process_keys(k, fn) for k in str_or_iter]
    if isinstance(str_or_iter, Mapping):
        return {fn(k): _process_keys(v, fn) for k, v in str_or_iter.items()}
    return str_or_iter

def _is_none(_in) -> str:
    """Determine if the input is None and returns a string with white-space removed.

    :param _in: input.

    :return:
        an empty sting if _in is None,
        else the input is returned with white-space removed
    """
    return "" if _in is None else re.sub(r"\s+", "", str(_in))

def camelize(str_or_iter: str | Iterable) -> str | Iterable:
    """Convert a string, dict, or list of dicts to camel case.

    Source: https://github.com/nficano/humps/blob/master/humps/main.py

    :param str_or_iter:
        A string or iterable.
    :type str_or_iter: Union[list, dict, str]
    :rtype: Union[list, dict, str]
    :returns:
        camelized string, dictionary, or list of dictionaries.
    """
    if isinstance(str_or_iter, (list, Mapping)):
        return _process_keys(str_or_iter, camelize)

    s = _is_none(str_or_iter)
    if s.isupper() or s.isnumeric():
        return str_or_iter

    if len(s) != 0 and not s[:2].isupper():
        s = s[0].lower() + s[1:]

    # For string "hello_world", match will contain
    #             the regex capture group for "_w".
    return UNDERSCORE_RE.sub(lambda m: m.group(0)[-1].upper(), s)


def to_camel(string) -> str | Iterable:
    """Convert a string to camel case."""
    return camelize(string)


class CamelModel(BaseModel):
    """Pydantic model that generated camelCase alias from snake_case field names."""
    class Config:
        alias_generator = to_camel
        population_by_name = True


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
    is_valid = False
    secret = os.environ.get(ENV_VAR_DOCQ_API_SECRET, None)
    if secret is not None or secret != "":
        is_valid = token == secret

    return is_valid


