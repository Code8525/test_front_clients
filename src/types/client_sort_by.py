from enum import Enum

from src.types.api_camel_enum import ApiCamelEnum


class ClientSortBy(ApiCamelEnum, Enum):
    """Поле сортировки списка клиентов. В Python — snake_case, в API — camelCase."""

    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    CLIENT_ID = "client_id"
    NAME = "name"
    FULL_NAME = "full_name"
    PARTY_TYPE = "party_type"
    INN = "inn"
    REGION_ID = "region_id"
    PARENT_ID = "parent_id"
