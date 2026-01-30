import uuid

from src.schemas.base import ResponseSchemaBase, SchemaBase


class Region(ResponseSchemaBase):
    """Ответ GET /api/regions — элемент списка для селекта «Регион»."""

    id: uuid.UUID
    name: str


class RegionsResponse(SchemaBase):
    """Ответ GET /api/regions — список регионов для селекта «Регион»."""

    items: list[Region]
