import logging
from typing import List

from sqlalchemy import delete
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session, query

from chanjo2.models.pydantic_models import Case, CaseCreate
from chanjo2.models.sql_models import Case as SQLCase

LOG = logging.getLogger("uvicorn.access")


def filter_cases_by_name(cases: query.Query, case_name: str) -> SQLCase:
    """Filter cases by case name."""
    return cases.filter(SQLCase.name == case_name).first()


def get_cases(db: Session, limit: int = 100) -> List[SQLCase]:
    """Return all cases."""
    return db.query(SQLCase).limit(limit).all()


def get_case(db: Session, case_name: str) -> Case:
    """Return a specific case by providing its name."""
    pipeline = {"filter_cases": filter_cases_by_name}
    query = db.query(SQLCase)

    return pipeline["filter_cases"](query, case_name)


def create_db_case(db: Session, case: CaseCreate) -> SQLCase:
    """Create a case."""
    db_case = SQLCase(name=case.name, display_name=case.display_name)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case


def count_cases(db: Session) -> int:
    return db.query(SQLCase).count()


def delete_case(db: Session, case_name: str) -> int:
    """Delete a case with the supplied name."""
    delete_stmt: Delete = delete(SQLCase).where(SQLCase.name == case_name)
    result: CursorResult = db.execute(delete_stmt)
    return result.rowcount
