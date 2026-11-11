"""A small dataclass base that builds typed objects from API JSON.

Unknown keys are kept (``to_dict()`` returns the full JSON, ``obj["key"]`` reads any key), so a
newer API adding fields never breaks an older SDK.
"""

from __future__ import annotations

import dataclasses
import types
import typing
from typing import Any, Literal, TypeVar, Union, get_args, get_origin, get_type_hints

T = TypeVar("T", bound="Model")

_INTERNAL = frozenset({"_raw", "last_response"})


@dataclasses.dataclass(kw_only=True)
class Model:
    _raw: dict[str, Any] = dataclasses.field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        hints = _hints(cls)
        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if f.name in _INTERNAL:
                continue
            if f.name in data:
                kwargs[f.name] = _decode(hints[f.name], data[f.name])
            elif f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
                kwargs[f.name] = None
        obj = cls(**kwargs)
        obj._raw = data
        return obj

    def to_dict(self) -> dict[str, Any]:
        """The JSON object this was built from."""
        return dict(self._raw)

    def __getitem__(self, key: str) -> Any:
        return self._raw[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._raw.get(key, default)


_HINTS: dict[type, dict[str, Any]] = {}


def _hints(cls: type) -> dict[str, Any]:
    hints = _HINTS.get(cls)
    if hints is None:
        hints = _HINTS[cls] = get_type_hints(cls)
    return hints


def _is_union(origin: Any) -> bool:
    return origin is Union or origin is types.UnionType


def _decode(tp: Any, value: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(tp)
    if _is_union(origin):
        args = [a for a in get_args(tp) if a is not type(None)]
        models = [a for a in args if isinstance(a, type) and issubclass(a, Model)]
        if isinstance(value, dict) and models:
            # Pick the first model whose required fields are all present.
            for m in models:
                if all(f.name in value for f in dataclasses.fields(m) if f.name not in _INTERNAL and _required(m, f)):
                    return m.from_dict(value)
            return models[-1].from_dict(value)
        for a in args:
            ao = get_origin(a)
            if isinstance(value, list) and ao in (list, tuple):
                return _decode(a, value)
            if isinstance(value, dict) and ao is dict:
                return _decode(a, value)
        return value
    if origin in (list, typing.List) and isinstance(value, list):  # noqa: UP006
        item_args = get_args(tp)
        item_tp = item_args[0] if item_args else Any
        return [_decode(item_tp, v) for v in value]
    if origin is tuple and isinstance(value, list):
        return tuple(value)
    if origin in (dict, typing.Dict) and isinstance(value, dict):  # noqa: UP006
        kv_args = get_args(tp)
        vt = kv_args[1] if len(kv_args) == 2 else Any
        return {k: _decode(vt, v) for k, v in value.items()}
    if origin is Literal:
        return value
    if isinstance(tp, type) and issubclass(tp, Model) and isinstance(value, dict):
        return tp.from_dict(value)
    return value


def _required(cls: type, f: dataclasses.Field[Any]) -> bool:
    hint = _hints(cls)[f.name]
    if _is_union(get_origin(hint)) and type(None) in get_args(hint):
        return False
    return f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING
