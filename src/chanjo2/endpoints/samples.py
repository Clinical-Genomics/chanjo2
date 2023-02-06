from pathlib import Path
from typing import List

from chanjo2.crud.samples import create_case_sample, get_case_samples, get_sample, get_samples
from chanjo2.dbutil import get_session
from chanjo2.models.pydantic_models import SampleCreate, SampleRead
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

router = APIRouter()


@router.post("/samples/", response_model=SampleRead)
def create_sample_for_case(
    sample: SampleCreate,
    db: Session = Depends(get_session),
):
    """Endpoint used to add a case sample to the database"""
    d4_file_path: Path = Path(sample.coverage_file_path)
    if not d4_file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not find file: { d4_file_path}",
        )
    db_sample = create_case_sample(db=db, sample=sample)
    if db_sample is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not find a case with name: {sample.case_name}",
        )
    return db_sample


@router.get("/samples/", response_model=List[SampleRead])
def read_samples(skip: int = 0, limit: int = 100, db: Session = Depends(get_session)):
    """Return all existing samples from the database."""
    return get_samples(db, skip=skip, limit=limit)


@router.get("/{case_name}/samples/", response_model=List[SampleRead])
def read_samples_for_case(case_name: str, db: Session = Depends(get_session)):
    """Return all samples for a given case from the database."""
    return get_case_samples(db, case_name=case_name)


@router.get("/samples/{sample_name}", response_model=SampleRead)
def read_sample(sample_name: str, db: Session = Depends(get_session)):
    db_sample = get_sample(db, sample_name=sample_name)
    if db_sample is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found")
    return db_sample
