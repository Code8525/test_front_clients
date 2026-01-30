import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from src.models.base import Base
from src.types.party_type import PartyType

if TYPE_CHECKING:
    from src.models.region_model import RegionModel


class ClientModel(Base):
    """Клиент: справочник с полями по ТЗ."""

    __tablename__ = "clients"

    client_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    party_type: Mapped[PartyType] = mapped_column(Enum(PartyType), nullable=False)
    inn: Mapped[str | None] = mapped_column(String(12), nullable=True)
    region_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("regions.id"),
        nullable=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("clients.client_id"),
        nullable=True,
    )

    region: Mapped["RegionModel | None"] = relationship("RegionModel", foreign_keys=[region_id])
    parent: Mapped["ClientModel | None"] = relationship(
        "ClientModel",
        remote_side=[client_id],
        foreign_keys=[parent_id],
    )
