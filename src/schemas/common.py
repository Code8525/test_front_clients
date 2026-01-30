from pydantic import Field

from src.schemas.base import SchemaBase
from src.types.sort_order import SortOrder


class PaginationParams(SchemaBase):
    """Параметры пагинации для GET /api/clients."""

    limit: int = Field(default=20, ge=1, le=100, description="Лимит записей")
    offset: int = Field(default=0, ge=0, description="Смещение")


class SortParams(SchemaBase):
    """Параметры сортировки для GET /api/clients."""

    sort_by: str = Field(default="created_at", description="Поле сортировки")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Направление")
