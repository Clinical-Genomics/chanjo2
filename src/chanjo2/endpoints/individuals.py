from pathlib import Path
from typing import List

from pyd4 import D4File
from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException, Query, status
from src.chanjo2.dependencies import get_session
from src.chanjo2.models.coverage_interval import CoverageInterval
from src.chanjo2.models.individuals import Individual, IndividualCreate, IndividualRead

router = APIRouter()


@router.post("/individuals/", response_model=IndividualRead)
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


@router.get("/individuals/", response_model=List[IndividualRead])
def read_individuals(
        *, session: Session = Depends(get_session), offset: int = 0, limit=Query(default=100, lte=100)
):
    return session.exec(select(Individual).offset(offset).limit(limit)).all()


@router.get("/individuals/{individual_id}", response_model=IndividualRead)
def read_individual(*, session: Session = Depends(get_session), individual_id: int):
    individual = session.get(Individual, individual_id)
    if not individual:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Individual not found")
    return individual


@router.get("/interval/{individual_id}/{chromosome}/{start}/{end}", response_model=CoverageInterval)
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
