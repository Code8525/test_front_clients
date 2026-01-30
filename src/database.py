from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import DATABASE_URL
from src.models.base import Base

# Импорт моделей, чтобы они зарегистрированы в Base.metadata перед create_all
from src.models.client_model import ClientModel  # noqa: F401
from src.models.region_model import RegionModel  # noqa: F401

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Зависимость для роутеров: сессия БД на запрос, закрывается после ответа."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Создание всех таблиц в SQLite по моделям. Вызывать при старте приложения."""
    Base.metadata.create_all(bind=engine)
