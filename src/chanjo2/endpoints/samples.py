from pathlib import Path
from typing import List

from chanjo2.dbutil import SessionLocal
from chanjo2.meta.handle_bed import parse_bed
from chanjo2.models.pydantic_models import CoverageInterval, SampleCreate, SampleRead
from fastapi import APIRouter, Depends, File, HTTPException, Query, status
from sqlmodel import Session, select

router = APIRouter()


@router.post("/sample_create/", response_model=SampleRead)
def create_sample(*, session: Session = Depends(SessionLocal), sample: SampleCreate):
    d4_file_path: Path = Path(sample.coverage_file_path)
    if not d4_file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not find file: {file}",
        )
    db_individual = Sample.from_orm(sample)
    session.add(db_individual)
    session.commit()
    session.refresh(db_individual)
    return db_individual


@router.get("/samples/", response_model=List[SampleRead])
def read_samples(
    *,
    session: Session = Depends(SessionLocal),
    offset: int = 0,
    limit=Query(default=100, lte=100),
):
    return session.exec(select(Sample).offset(offset).limit(limit)).all()


@router.get("/sample/{sample_id}", response_model=SampleRead)
def read_individual(*, session: Session = Depends(SessionLocal), sample_id: str):
    sample = session.exec(select(Sampke).filter(sample_id == sample_id)).first()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    return sample


@router.get("/interval/{sample_id}/", response_model=CoverageInterval)
def read_interval(
    *,
    session: Session = Depends(SessionLocal),
    sample_id: str,
    chromosome: str,
    start: int,
    end: int,
):
    sample = session.exec(select(Individual).filter(sample_id == sample_id)).first()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    coverage_file: D4File = D4File(sample.coverage_file_path)
    res: List[float] = coverage_file.mean([(chromosome, start, end)])
    interval_id: str = f"{chromosome}:{start}-{end}"
    return CoverageInterval(
        chromosome=chromosome,
        start=start,
        end=end,
        sample_id=individual.individual_id,
        interval_id=interval_id,
        mean_coverage=res[0],
    )


@router.get("/{sample_id}/target_coverage", response_model=List[float])
def read_target_coverage(
    *,
    session: Session = Depends(SessionLocal),
    sample_id: str,
):
    sample = session.exec(select(Individual).filter(sample_id == sample_id)).first()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    coverage_file: D4File = D4File(sample.coverage_file_path)
    with open(sample.region_file_path, "rb") as default_region_file:
        regions: List[tuple[str, int, int]] = parse_bed(bed_file=default_region_file.read())
    coverage_results: List[float] = coverage_file.mean(regions=regions)
    return coverage_results


@router.post("/interval_file/{sample_id}/", response_model=List[float])
def read_bed_intervals(
    *,
    session: Session = Depends(SessionLocal),
    sample_id: str,
    interval_file: bytes = File(...),
):
    sample = session.exec(select(Sample).filter(sampple_id == sample_id)).first()
    if not sample:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    coverage_file: D4File = D4File(sample.coverage_file_path)
    regions: List[tuple[str, int, int]] = parse_bed(bed_file=interval_file)
    coverage_results: List[float] = coverage_file.mean(regions=regions)
    return coverage_results
