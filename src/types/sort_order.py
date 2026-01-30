from enum import Enum

from src.types.api_camel_enum import ApiCamelEnum


class SortOrder(ApiCamelEnum, Enum):
    """Направление сортировки. В Python — snake_case, в API — camelCase."""

    ASC = "asc"
    DESC = "desc"
