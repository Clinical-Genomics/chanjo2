from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.chanjo2.dependencies import get_session
from src.chanjo2.models.regions import Region, RegionRead, RegionCreate
from sqlmodel import Session, select

router = APIRouter()


@router.post("/regions/", response_model=RegionRead)
def create_region(*, session: Session = Depends(get_session), region: RegionCreate):
    db_region = Region.from_orm(region)
    session.add(db_region)
    session.commit()
    session.refresh(db_region)
    return db_region


@router.get("/regions/", response_model=List[RegionRead])
def read_regions(
        *, session: Session = Depends(get_session), offset: int = 0, limit=Query(default=100, lte=100)
):
    return session.exec(select(Region).offset(offset).limit(limit)).all()


@router.get("/regions/{region_id}", response_model=RegionRead)
def read_region(*, session: Session = Depends(get_session), region_id: int):
    region = session.get(Region, region_id)
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    return region
