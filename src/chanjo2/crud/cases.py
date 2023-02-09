import logging
from typing import List

from chanjo2.models.pydantic_models import Case, CaseCreate
from chanjo2.models.sql_models import Case as SQLCase
from sqlalchemy.orm import Session, query

LOG = logging.getLogger("uvicorn.access")


def _filter_cases_by_name(cases: query.Query, case_name: str, **kwargs) -> SQLCase:
    """Filter cases by case name"""
    return cases.filter(SQLCase.name == case_name).first()


def get_cases(db: Session, skip: int = 0, limit: int = 100) -> List[Case]:
    """Return all cases."""
    return db.query(SQLCase).offset(skip).limit(limit).all()


def get_case(db: Session, case_name: str) -> Case:
    """Return a specific case by providing its name."""

    pipeline = {"filter_cases": _filter_cases_by_name}
    query = db.query(SQLCase)

    return pipeline["filter_cases"](query, case_name)


def create_db_case(db: Session, case: CaseCreate) -> Case:
    """Create a case."""
    db_case = SQLCase(name=case.name, display_name=case.display_name)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case
