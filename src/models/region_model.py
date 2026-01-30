import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from src.models.base import Base


class RegionModel(Base):
    """Справочник регионов — для селекта «Регион» (кеш на фронте)."""

    __tablename__ = "regions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
