"""Базовые классы для всех API-схем. Сериализация в camelCase для фронта."""

from pydantic import BaseModel, ConfigDict


def to_camel(name: str) -> str:
    """snake_case → camelCase (например, client_id → clientId)."""
    parts = name.split("_")
    return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])


class SchemaBase(BaseModel):
    """
    Базовая схема для всех API-моделей.
    - Алиасы в camelCase для JSON (фронт).
    - populate_by_name=True: приём и snake_case, и camelCase во входящих данных.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ResponseSchemaBase(SchemaBase):
    """
    База для схем-ответов, строящихся из ORM (from_attributes=True).
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
