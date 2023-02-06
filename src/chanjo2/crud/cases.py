from typing import List

from chanjo2.models.pydantic_models import Case, CaseCreate
from chanjo2.models.sql_models import Case as SQLCase
from sqlalchemy.orm import Session


def get_cases(db: Session, skip: int = 0, limit: int = 100) -> List[Case]:
    """Return all cases."""
    return db.query(SQLCase).offset(skip).limit(limit).all()


def get_case(db: Session, case_name: str) -> Case:
    """Return a specific case by providing its name"""
    return db.query(SQLCase).filter(SQLCase.name == case_name).first()


def case_create(db: Session, case: CaseCreate) -> Case:
    """Create a case"""
    db_case = SQLCase(name=case.name, display_name=case.display_name)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case
