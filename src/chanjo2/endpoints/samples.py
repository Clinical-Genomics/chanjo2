from pathlib import Path
from typing import List

from chanjo2.dbutil import get_session
from chanjo2.meta.handle_bed import parse_bed
from chanjo2.models.pydantic_models import CoverageInterval, SampleCreate, SampleRead
from fastapi import APIRouter, Depends, File, HTTPException, Query, status
from sqlmodel import Session, select

router = APIRouter()


@router.post("/sample_create/", response_model=SampleRead)
def create_sample(*, session: Session = Depends(get_session), sample: SampleCreate):
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
    session: Session = Depends(get_session),
    offset: int = 0,
    limit=Query(default=100, lte=100),
):
    return session.exec(select(Sample).offset(offset).limit(limit)).all()


@router.get("/sample/{sample_id}", response_model=SampleRead)
def read_individual(*, session: Session = Depends(get_session), sample_id: str):
    sample = session.exec(select(Sampke).filter(sample_id == sample_id)).first()
    if not sample:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found"
        )
    return sample
