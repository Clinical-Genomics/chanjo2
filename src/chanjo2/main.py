from pathlib import Path
from typing import List, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pyd4 import D4File
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, select

from chanjo2.dependencies import engine, get_session


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


##


class IndividualBase(SQLModel):
    individual_id: str
    coverage_file_path: str


class Individual(IndividualBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class IndividualCreate(IndividualBase):
    pass


class IndividualRead(IndividualBase):
    id: int


class CoverageInterval(BaseModel):
    chromosome: str
    start: int
    end: int
    individual_id: str
    interval_id: str
    mean_coverage: float


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/individuals/", response_model=IndividualRead)
def create_individual(*, session: Session = Depends(get_session), individual: IndividualCreate):
    file_path: Path = Path(individual.coverage_file_path)
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not find coverage file"
        )
    individual.coverage_file_path = file_path.as_posix()
    db_individual = Individual.from_orm(individual)
    session.add(db_individual)
    session.commit()
    session.refresh(db_individual)
    return db_individual


@app.get("/individuals/", response_model=List[IndividualRead])
def read_individuals(
    *, session: Session = Depends(get_session), offset: int = 0, limit=Query(default=100, lte=100)
):
    individuals = session.exec(select(Individual).offset(offset).limit(limit)).all()
    return individuals


@app.get("/individuals/{individual_id}", response_model=IndividualRead)
def read_individual(*, session: Session = Depends(get_session), individual_id: int):
    individual = session.get(Individual, individual_id)
    if not individual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Individual not found")
    return individual


##


@app.get("/interval/{individual_id}/{chromosome}/{start}/{end}", response_model=CoverageInterval)
def read_interval(
    *,
    session: Session = Depends(get_session),
    individual_id: int,
    chromosome: str,
    start: int,
    end: int,
):
    individual = session.get(Individual, individual_id)
    if not individual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Individual not found")
    coverage_file = D4File(individual.coverage_file_path)
    res: List[float] = coverage_file.mean([(chromosome, start, end)])
    interval_id: str = f"{chromosome}:{start}-{end}"
    return CoverageInterval(
        chromosome=chromosome,
        start=start,
        end=end,
        individual_id=individual.individual_id,
        interval_id=interval_id,
        mean_coverage=res[0],
    )


##


@app.post("/regions/", response_model=RegionRead)
def create_region(*, session: Session = Depends(get_session), region: RegionCreate):
    db_region = Region.from_orm(region)
    session.add(db_region)
    session.commit()
    session.refresh(db_region)
    return db_region


@app.get("/regions/", response_model=List[RegionRead])
def read_regions(
    *, session: Session = Depends(get_session), offset: int = 0, limit=Query(default=100, lte=100)
):
    regions = session.exec(select(Region).offset(offset).limit(limit)).all()
    return regions


@app.get("/regions/{region_id}", response_model=RegionRead)
def read_region(*, session: Session = Depends(get_session), region_id: int):
    region = session.get(Region, region_id)
    if not region:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")
    return region
