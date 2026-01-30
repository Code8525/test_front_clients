"""Базовый класс для API-enum: внутри Python — snake_case, в JSON/API — camelCase."""

from __future__ import annotations

import re
from enum import Enum
from typing import ClassVar, cast

from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.alias_generators import to_camel, to_snake
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

_SNAKE_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
_CAMEL_RE = re.compile(r"^[a-z]+(?:[A-Z][a-z0-9]*)*$")


def _normalize_in_strict(s: str) -> str:
    if _SNAKE_RE.fullmatch(s):
        return s
    if _CAMEL_RE.fullmatch(s):
        return to_snake(s)
    raise ValueError("Only camelCase or snake_case are allowed")


class ApiCamelEnum:
    """
    Использование: class SomeEnum(ApiCamelEnum, Enum): ...
    - Внутри Python: member.value = snake_case (строка)
    - Вход из API: camelCase или snake_case
    - Выход в JSON: camelCase
    - OpenAPI/Swagger: выпадающий список с camelCase значениями
    """

    _lookup_in: ClassVar[dict[str, ApiCamelEnum]]
    _api_out: ClassVar[dict[ApiCamelEnum, str]]
    _allowed_api_values: ClassVar[list[str]]

    @classmethod
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if not issubclass(cls, Enum) or not hasattr(cls, "__members__"):
            return

        lookup: dict[str, ApiCamelEnum] = {}
        out_map: dict[ApiCamelEnum, str] = {}
        api_values: list[str] = []

        for member in cls.__members__.values():
            m_enum = member
            snake_val_obj = m_enum.value

            if not isinstance(snake_val_obj, str):
                raise TypeError(
                    f"{cls.__name__} should use string values in snake_case, "
                    f"got {type(snake_val_obj).__name__}"
                )
            snake_val: str = snake_val_obj

            if not _SNAKE_RE.fullmatch(snake_val):
                raise ValueError(
                    f"{cls.__name__}.{m_enum.name} value must be snake_case string, got {snake_val!r}"
                )

            camel_val: str = to_camel(snake_val)

            lookup[snake_val] = member
            lookup[to_snake(camel_val)] = member

            out_map[member] = camel_val
            api_values.append(camel_val)

        cls._lookup_in = lookup
        cls._api_out = out_map
        cls._allowed_api_values = sorted(set(api_values))

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: type, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def _validate(v: object) -> ApiCamelEnum:
            if isinstance(v, cls):
                return cast(ApiCamelEnum, v)
            if isinstance(v, str):
                try:
                    key = _normalize_in_strict(v)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid {cls.__name__}: {v!r}. Only camelCase or snake_case are allowed."
                    ) from e
                m = cls._lookup_in.get(key)
                if m is not None:
                    return m
            raise ValueError(
                f"Invalid {cls.__name__}: {v!r}. Allowed: {', '.join(cls._allowed_api_values)}"
            )

        return core_schema.no_info_after_validator_function(
            function=_validate,
            schema=core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                function=lambda e: cls._api_out[cast(ApiCamelEnum, e)],
                return_schema=core_schema.str_schema(),
                info_arg=False,
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        schema: JsonSchemaValue = handler(core_schema.str_schema())
        schema.update({"enum": cls._allowed_api_values})
        return schema

    @classmethod
    def from_api(cls, s: str) -> ApiCamelEnum:
        key = _normalize_in_strict(s)
        m = cls._lookup_in.get(key)
        if m is None:
            raise ValueError(
                f"Invalid {cls.__name__}: {s!r}. Allowed: {cls._allowed_api_values}"
            )
        return m
