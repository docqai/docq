"""Domain classes for Docq."""

from dataclasses import dataclass
from typing import Any, Optional

from .config import FeatureType, SpaceType

_SEPARATOR_FOR_STR = ":"
_SEPARATOR_FOR_VALUE = "_"
_DEFAULT_SEPARATOR = _SEPARATOR_FOR_STR


def _join_properties(separator: str = _DEFAULT_SEPARATOR, *args: Optional[Any]) -> str:
    return separator.join([str(arg) for arg in args])


@dataclass
class FeatureKey:
    """Feature key."""

    type_: FeatureType
    id_: int

    def __str__(self) -> str:
        return _join_properties(_SEPARATOR_FOR_STR, self.type_.name, self.id_)

    def value(self) -> str:
        return _join_properties(_SEPARATOR_FOR_VALUE, self.type_.name, self.id_)


@dataclass
class SpaceKey:
    """Space key."""

    type_: SpaceType
    id_: int

    def __str__(self) -> str:
        return _join_properties(_SEPARATOR_FOR_STR, self.type_.name, self.id_)

    def value(self) -> str:
        return _join_properties(_SEPARATOR_FOR_VALUE, self.type_.name, self.id_)


@dataclass
class ConfigKey:
    """Config key."""

    key: str
    name: str
    is_optional: bool = False
    is_secret: bool = False
    ref_link: str = None
