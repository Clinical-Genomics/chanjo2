from typing import List

from chanjo2.crud.cases import case_create, get_case, get_cases
from chanjo2.dbutil import get_session
from chanjo2.models.pydantic_models import CaseCreate, CaseRead
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

router = APIRouter()


@router.post("/cases/", response_model=CaseRead)
def create_case(case: CaseCreate, db: Session = Depends(get_session)):
    """Add a case to the database"""
    db_case = get_case(db, case_name=case.name)
    if db_case:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Case already registered"
        )
    return case_create(db=db, case=case)


@router.get("/cases/", response_model=List[CaseRead])
def read_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_session)):
    """Endpoint used to fetch all existing cases from the database"""
    return get_cases(db, skip=skip, limit=limit)


@router.get("/cases/{case_name}", response_model=CaseRead)
def read_case(case_name: str, db: Session = Depends(get_session)):
    """Endpoint used to fetch one cases from the database by providing its ID"""
    db_case = get_case(db, case_name=case_name)
    if db_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return db_case
