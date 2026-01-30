from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.region_model import RegionModel
from src.schemas.region import Region, RegionsResponse

router = APIRouter()


@router.get("", response_model=RegionsResponse)
def list_regions(db: Session = Depends(get_db)) -> RegionsResponse:
    """Список регионов для селекта Регион."""
    regions = db.query(RegionModel).order_by(RegionModel.name).all()
    return RegionsResponse(items=[RegionModel.model_validate(r) for r in regions])
