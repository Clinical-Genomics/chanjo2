from typing import Optional, Literal, List

from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlmodel import Field, Session, SQLModel, select

from chanjo2.dependencies import get_session, engine

class RegionBase(SQLModel):
    name: str
    file_path: str
    version: int = 1
    genome_build: str

class Region(RegionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class RegionCreate(RegionBase):
    pass

class RegionRead(RegionBase):
    id: int

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()



@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/regions/", response_model=RegionRead)
def create_region(*, session: Session = Depends(get_session), region: RegionCreate):
    db_region = Region.from_orm(region)
    session.add(db_region)
    session.commit()
    session.refresh(db_region)
    return db_region

@app.get("/regions/", response_model=List[RegionRead])
def read_regions(*, session: Session = Depends(get_session), offset: int = 0, limit = Query(default=100, lte=100)):
    regions = session.exec(select(Region).offset(offset).limit(limit)).all()
    return regions

@app.get("/regions/{region_id}", response_model=RegionRead)
def read_region(*, session: Session = Depends(get_session), region_id: int):
    region = session.get(Region, region_id)
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    return region