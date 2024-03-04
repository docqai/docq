"""Utilities for the API handlers."""
import re
from typing import Any, Iterable, Mapping

from pydantic import BaseModel

UNDERSCORE_RE = re.compile(r"(?<=[^\-_])[\-_]+[^\-_]")


def _process_keys(str_or_iter: str | Iterable, fn: Any) -> str | Iterable:
    """Recursively process keys in a string, dict, or list of dicts."""
    if isinstance(str_or_iter, list):
        return [_process_keys(k, fn) for k in str_or_iter]
    if isinstance(str_or_iter, Mapping):
        return {fn(k): _process_keys(v, fn) for k, v in str_or_iter.items()}
    return str_or_iter


def _is_none(_in: Any) -> str:
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


def to_camel(string: str) -> str | Iterable:
    """Convert a string to camel case."""
    return camelize(string)


class CamelModel(BaseModel):
    """Pydantic model that generated camelCase alias from snake_case field names."""

    class Config:
        """Pydantic model configuration."""

        alias_generator = to_camel
        population_by_name = True
