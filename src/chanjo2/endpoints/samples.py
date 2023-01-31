from pathlib import Path
from typing import List

from chanjo2.constants import BAD_REQUEST, NOT_FOUND
from chanjo2.crud import samples as crud_samples
from chanjo2.dbutil import get_session
from chanjo2.models import pydantic_models, sql_models
from fastapi import APIRouter, Depends, File, HTTPException, status
from sqlmodel import Session

router = APIRouter()

### Case endpoints
@router.post("/cases/", response_model=pydantic_models.CaseRead)
def create_case(case: pydantic_models.CaseCreate, db: Session = Depends(get_session)):
    """Endpoint used to add a case to the database"""
    db_case = crud_samples.get_case(db, case_name=case.name)
    if db_case:
        raise HTTPException(status_code=BAD_REQUEST, detail="Case already registered")
    return crud_samples.create_case(db=db, case=case)


@router.get("/cases/", response_model=List[pydantic_models.CaseRead])
def read_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_session)):
    """Endpoint used to fetch all existing cases from the database"""
    cases = crud_samples.get_cases(db, skip=skip, limit=limit)
    return cases


@router.get("/cases/{case_name}", response_model=pydantic_models.CaseRead)
def read_case(case_name: str, db: Session = Depends(get_session)):
    """Endpoint used to fetch one cases from the database by providing its ID"""
    db_case = crud_samples.get_case(db, case_name=case_name)
    if db_case is None:
        raise HTTPException(status_code=NOT_FOUND, detail="Case not found")
    return db_case


### Sample endpoints
@router.post("/samples/", response_model=pydantic_models.SampleRead)
def create_sample_for_case(
    sample: pydantic_models.SampleCreate,
    db: Session = Depends(get_session),
):
    """Endpoint used to add a case sample to the database"""
    d4_file_path: Path = Path(sample.coverage_file_path)
    if not d4_file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not find file: { d4_file_path}",
        )
    updated_case = crud_samples.create_case_sample(db=db, sample=sample)
    if updated_case is None:
        raise HTTPException(
            status_code=NOT_FOUND, detail="Could not find a case for this sample"
        )
    return updated_case


@router.get("/{case_id}/samples/", response_model=List[pydantic_models.SampleRead])
def read_samples_for_case(case_id: int, db: Session = Depends(get_session)):
    """Endpoint used to fetch all samples for a given case from the database"""
    samples = crud_samples.get_case_samples(db, case_id=case_id)
    return samples


@router.get("/samples/", response_model=List[pydantic_models.SampleRead])
def read_samples(skip: int = 0, limit: int = 100, db: Session = Depends(get_session)):
    """Endpoint used to fetch all existing samples from the database"""
    samples = crud_samples.get_samples(db, skip=skip, limit=limit)
    return samples


@router.get("/samples/{sample_id}", response_model=pydantic_models.SampleRead)
def read_sample(sample_id: int, db: Session = Depends(get_session)):
    db_sample = crud_samples.get_case(db, sample_id=sample_id)
    if db_sample is None:
        raise HTTPException(status_code=NOT_FOUND, detail="Sample not found")
    return db_sample
