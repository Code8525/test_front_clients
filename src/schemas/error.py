from pydantic import Field

from src.schemas.base import SchemaBase


class ErrorDetail(SchemaBase):
    """Одно поле ошибки валидации: где и что."""

    field: str = Field(..., description="Где произошло (например, body.inn)")
    message: str = Field(..., description="Текст ошибки")


class ErrorResponse(SchemaBase):
    """Единый формат ответа об ошибке API."""

    error_name: str = Field(..., description="Код типа ошибки")
    message: str = Field(..., description="Сообщение для пользователя")
    errors: list[ErrorDetail] | None = Field(default=None, description="Детали по полям (для валидации)")
