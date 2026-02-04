import uuid
from datetime import datetime

from pydantic import Field

from src.schemas.base import ResponseSchemaBase, SchemaBase
from src.types.client_sort_by import ClientSortBy
from src.types.party_type import PartyType
from src.types.sort_order import SortOrder


class ClientListQuery(SchemaBase):
    """Query-параметры GET /api/clients — фильтры, пагинация, сортировка."""

    query: str | None = Field(default=None, description="Поиск по имени, ИНН, full_name")
    parent_id: uuid.UUID | None = Field(default=None)
    region_id: uuid.UUID | None = Field(default=None)
    party_type: PartyType | None = Field(default=None)
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: ClientSortBy = Field(default=ClientSortBy.CREATED_AT)
    sort_order: SortOrder = Field(default=SortOrder.DESC)


class ClientCreate(SchemaBase):
    """Body POST /api/clients — создание клиента."""

    name: str = Field(..., max_length=255)
    full_name: str | None = Field(default=None, max_length=512)
    party_type: PartyType
    inn: str | None = Field(default=None, max_length=12)
    region_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None


class ClientUpdate(SchemaBase):
    """Body PATCH /api/clients/{client_id} — частичное обновление."""

    name: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=512)
    party_type: PartyType | None = None
    inn: str | None = Field(default=None, max_length=12)
    region_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None


class Client(ResponseSchemaBase):
    """Ответ GET по client_id и элемент списка GET /api/clients."""

    client_id: uuid.UUID
    name: str
    full_name: str | None
    party_type: PartyType
    inn: str | None
    created_at: datetime
    updated_at: datetime
    region_id: uuid.UUID | None
    parent_id: uuid.UUID | None


class ClientsResponse(SchemaBase):
    """Ответ GET /api/clients — список с total."""

    items: list[Client]
    total: int


class ClientParentsResponse(SchemaBase):
    """Ответ GET /api/clients/parents — список головных клиентов для селекта."""

    items: list[Client]
    total: int
