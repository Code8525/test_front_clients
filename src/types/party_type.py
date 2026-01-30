from enum import Enum

from src.types.api_camel_enum import ApiCamelEnum


class PartyType(ApiCamelEnum, Enum):
    """Тип стороны: физ. лицо или юр. лицо. В Python — snake_case, в API — camelCase."""

    INDIVIDUAL = "individual"
    LEGAL = "legal"
