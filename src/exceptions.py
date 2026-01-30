"""Кастомные исключения для единого формата ответов API.

На каждую бизнес-ошибку — отдельный класс, наследующийся от BusinessError.
Обработчики в main.py преобразуют их в единый формат ответа (error_name, message, details).
"""


class BusinessError(Exception):
    """Базовый класс бизнес-исключений API. Подкласс обязан задать DEFAULT_MESSAGE."""

    MESSAGE = ""
    STATUS_CODE = 409

    def __init__(
        self,
        message: str | None = None,
        status_code: int | None = None,
    ) -> None:
        if message is not None:
            self.message = message
        else:
            default = self.__class__.MESSAGE
            if not default:
                raise TypeError(
                    f"{self.__class__.__name__} должен определять DEFAULT_MESSAGE"
                )
            self.message = default
        self.status_code = status_code if status_code is not None else self.STATUS_CODE
        super().__init__(self.message)


class ClientAlreadyExists(BusinessError):
    """Клиент уже существует в базе."""
    MESSAGE = "Клиент уже существует в базе"


class ClientAlreadyExistsByInn(BusinessError):
    """Клиент с таким ИНН уже существует в базе."""
    MESSAGE = "Клиент с таким ИНН уже существует в базе"


class ClientNotFound(BusinessError):
    """Клиент не найден."""
    MESSAGE = "Клиент не найден"
    STATUS_CODE = 404


class ParentClientNotFound(BusinessError):
    """Родительский клиент не найден."""
    MESSAGE = "Родительский клиент не найден"
    STATUS_CODE = 404
