from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from chanjo2.crud.samples import (
    create_sample_in_case,
    delete_sample,
    get_case_samples,
    get_sample,
    get_samples,
)
from chanjo2.dbutil import get_session
from chanjo2.models.pydantic_models import Sample, SampleCreate

router = APIRouter()


@router.post("/samples/", response_model=Sample)
def create_sample_for_case(
    sample: SampleCreate,
    db: Session = Depends(get_session),
):
    """Add a sample to a case in the database."""
    result: Union[SQLSample, str] = create_sample_in_case(db=db, sample=sample)
    if isinstance(result, str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=result
        )
    return result


@router.get("/samples/", response_model=List[Sample])
def read_samples(limit: int = 100, db: Session = Depends(get_session)):
    """Return all existing samples from the database."""
    return get_samples(db, limit=limit)


@router.get("/{case_name}/samples/", response_model=List[Sample])
def read_samples_for_case(case_name: str, db: Session = Depends(get_session)):
    """Return all samples for a given case from the database."""
    return get_case_samples(db, case_name=case_name)


@router.get("/samples/{sample_name}", response_model=Sample)
def read_sample(sample_name: str, db: Session = Depends(get_session)):
    """Return a sample by providing its name"""
    db_sample = get_sample(db, sample_name=sample_name)
    if db_sample is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sample not found"
        )
    return db_sample


@router.delete("/samples/delete/{sample_name}", response_model=str)
def delete_db_sample(sample_name: str, db: Session = Depends(get_session)):
    """Delete a sample with the provided name."""
    return f"Removing sample {sample_name}. Affected rows: {delete_sample(db=db, sample_name=sample_name)}"
