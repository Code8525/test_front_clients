import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from src.database import get_db
from src.exceptions import (
    ClientAlreadyExists,
    ClientAlreadyExistsByInn,
    ClientNotFound,
    ParentClientNotFound,
)
from src.models.client_model import ClientModel
from src.schemas.client import (
    ClientCreate,
    ClientListQuery,
    Client,
    ClientsResponse,
    ClientUpdate,
)
from src.types.client_sort_by import ClientSortBy
from src.types.sort_order import SortOrder

router = APIRouter()


def _ensure_parent_exists(parent_id: uuid.UUID | None, db: Session) -> None:
    """Проверка, что родительский клиент существует. При отсутствии — ParentClientNotFound."""
    if parent_id is None:
        return
    if not db.query(ClientModel).filter(ClientModel.client_id == parent_id).first():
        raise ParentClientNotFound()


def _ensure_client_unique_on_create(body: ClientCreate, db: Session) -> None:
    """Проверка уникальности имени и ИНН при создании. При дубликате — ClientAlreadyExists / ClientAlreadyExistsByInn."""
    if body.inn and db.query(ClientModel).filter(ClientModel.inn == body.inn).first():
        raise ClientAlreadyExistsByInn()
    if db.query(ClientModel).filter(ClientModel.name == body.name).first():
        raise ClientAlreadyExists()


def _ensure_client_unique_on_update(
    client_id: uuid.UUID,
    data: dict,
    db: Session,
) -> None:
    """Проверка уникальности имени и ИНН при обновлении. При дубликате — ClientAlreadyExists / ClientAlreadyExistsByInn."""
    if data.get("inn"):
        other = db.query(ClientModel).filter(ClientModel.client_id != client_id, ClientModel.inn == data["inn"]).first()
        if other:
            raise ClientAlreadyExistsByInn()
    if "name" in data:
        other = db.query(ClientModel).filter(ClientModel.client_id != client_id, ClientModel.name == data["name"]).first()
        if other:
            raise ClientAlreadyExists()


@router.get("", response_model=ClientsResponse)
def list_clients(
    params: Annotated[ClientListQuery, Query()],
    db: Session = Depends(get_db),
) -> ClientsResponse:
    """Список клиентов с фильтрами, пагинацией и сортировкой."""
    q = db.query(ClientModel)
    if params.query:
        search = f"%{params.query}%"
        q = q.filter(
            or_(
                ClientModel.name.ilike(search),
                ClientModel.full_name.ilike(search),
                ClientModel.inn.ilike(search),
            )
        )
    if params.parent_id is not None:
        q = q.filter(ClientModel.parent_id == params.parent_id)
    if params.region_id is not None:
        q = q.filter(ClientModel.region_id == params.region_id)
    if params.party_type is not None:
        q = q.filter(ClientModel.party_type == params.party_type)
    total = q.count()
    order_col = getattr(ClientModel, params.sort_by.value, ClientModel.created_at)
    if params.sort_order == SortOrder.DESC:
        order_col = order_col.desc()
    else:
        order_col = order_col.asc()
    items = q.order_by(order_col).offset(params.offset).limit(params.limit).all()
    return ClientsResponse(
        items=[Client.model_validate(c) for c in items],
        total=total,
    )


@router.get("/{client_id}", response_model=Client)
def get_client(client_id: uuid.UUID, db: Session = Depends(get_db)) -> Client:
    """Один клиент по client_id."""
    client = db.query(ClientModel).filter(ClientModel.client_id == client_id).first()
    if not client:
        raise ClientNotFound()
    return ClientModel.model_validate(client)


@router.post("", response_model=Client, status_code=201)
def create_client(body: ClientCreate, db: Session = Depends(get_db)) -> Client:
    """Создание клиента."""
    _ensure_client_unique_on_create(body, db)
    _ensure_parent_exists(body.parent_id, db)
    client = ClientModel(
        name=body.name,
        full_name=body.full_name,
        party_type=body.party_type,
        inn=body.inn,
        region_id=body.region_id,
        parent_id=body.parent_id,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return ClientModel.model_validate(client)


@router.patch("/{client_id}", response_model=Client)
def update_client(
    client_id: uuid.UUID,
    body: ClientUpdate,
    db: Session = Depends(get_db),
) -> Client:
    """Частичное обновление клиента."""
    client = db.query(ClientModel).filter(ClientModel.client_id == client_id).first()
    if not client:
        raise ClientNotFound()
    data = body.model_dump(exclude_unset=True)
    _ensure_client_unique_on_update(client_id, data, db)
    _ensure_parent_exists(data.get("parent_id"), db)
    for key, value in data.items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return ClientModel.model_validate(client)


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Удаление клиента."""
    client = db.query(ClientModel).filter(ClientModel.client_id == client_id).first()
    if not client:
        raise ClientNotFound()
    db.delete(client)
    db.commit()
