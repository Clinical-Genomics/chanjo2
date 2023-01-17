from pathlib import Path
from typing import List

from chanjo2.dbutil import get_session
from chanjo2.meta.handle_bed import parse_bed
from chanjo2.models.coverage_interval import CoverageInterval
from chanjo2.models.individuals import Individual, IndividualCreate, IndividualRead
from fastapi import APIRouter, Depends, File, HTTPException, Query, status
from sqlmodel import Session, select

router = APIRouter()


@router.post("/individuals/", response_model=IndividualRead)
def create_individual(
    *, session: Session = Depends(get_session), individual: IndividualCreate
):
    d4_file_path: Path = Path(individual.coverage_file_path)
    region_path: Path = Path(individual.region_file_path)
    for file in [d4_file_path, region_path]:
        if not file.is_file():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not find file: {file}",
            )
    db_individual = Individual.from_orm(individual)
    session.add(db_individual)
    session.commit()
    session.refresh(db_individual)
    return db_individual


@router.get("/individuals/", response_model=List[IndividualRead])
def read_individuals(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit=Query(default=100, lte=100),
):
    return session.exec(select(Individual).offset(offset).limit(limit)).all()


@router.get("/individuals/{individual_id}", response_model=IndividualRead)
def read_individual(*, session: Session = Depends(get_session), individual_id: str):
    individual = session.exec(
        select(Individual).filter(individual_id == individual_id)
    ).first()
    if not individual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Individual not found"
        )
    return individual


@router.get("/interval/{individual_id}/", response_model=CoverageInterval)
def read_interval(
    *,
    session: Session = Depends(get_session),
    individual_id: str,
    chromosome: str,
    start: int,
    end: int,
):
    individual = session.exec(
        select(Individual).filter(individual_id == individual_id)
    ).first()
    if not individual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Individual not found"
        )
    coverage_file: D4File = D4File(individual.coverage_file_path)
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


@router.get("/{individual_id}/target_coverage", response_model=List[float])
def read_target_coverage(
    *,
    session: Session = Depends(get_session),
    individual_id: str,
):
    individual = session.exec(
        select(Individual).filter(individual_id == individual_id)
    ).first()
    if not individual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Individual not found"
        )
    coverage_file: D4File = D4File(individual.coverage_file_path)
    with open(individual.region_file_path, "rb") as default_region_file:
        regions: List[tuple[str, int, int]] = parse_bed(
            bed_file=default_region_file.read()
        )
    coverage_results: List[float] = coverage_file.mean(regions=regions)
    return coverage_results


@router.post("/interval_file/{individual_id}/", response_model=List[float])
def read_bed_intervals(
    *,
    session: Session = Depends(get_session),
    individual_id: str,
    interval_file: bytes = File(...),
):
    individual = session.exec(
        select(Individual).filter(individual_id == individual_id)
    ).first()
    if not individual:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Individual not found"
        )
    coverage_file: D4File = D4File(individual.coverage_file_path)
    regions: List[tuple[str, int, int]] = parse_bed(bed_file=interval_file)
    coverage_results: List[float] = coverage_file.mean(regions=regions)
    return coverage_results
