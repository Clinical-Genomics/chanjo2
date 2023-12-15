from typing import List, Union

from sqlalchemy import delete
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.orm import Session, query

from chanjo2.models import CaseSample, SQLCase, SQLSample
from chanjo2.models.pydantic_models import Case, CaseCreate


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


def delete_entry(db: Session, table: Union[SQLCase, SQLSample], id: int) -> int:
    """Deletes a Sample or Case entry from the database."""
    delete_stmt: Delete = delete(table).where(table.id == id)
    result: CursorResult = db.execute(delete_stmt)
    db.commit()
    return result.rowcount


def delete_case_sample_ref(db: Session, case_id: int, sample_id: int) -> int:
    """Delete the association of a Sample to a Case in the CaseSample table."""
    delete_stmt: Delete = delete(CaseSample).where(
        CaseSample.c.case_id == case_id, CaseSample.c.sample_id == sample_id
    )
    result: CursorResult = db.execute(delete_stmt)
    db.commit()
    return result.rowcount


def delete_case(db: Session, case_name: str) -> int:
    """Delete a case with the supplied name."""
    db_case: SQLCase = db.query(SQLCase).where(SQLCase.name == case_name).first()

    # Delete samples linked uniquely to this case
    if db_case is None:
        return 0

    for db_sample in db_case.samples:
        nr_linked_cases: int = (
            db.query(CaseSample).where(CaseSample.c.sample_id == db_sample.id).count()
        )
        # Remove case-sample association in CaseSample table:
        delete_case_sample_ref(db=db, case_id=db_case.id, sample_id=db_sample.id)

        if nr_linked_cases == 1:  # Sample linked only to this case
            delete_entry(db=db, table=SQLSample, id=db_sample.id)

    # Delete case
    return delete_entry(db=db, table=SQLCase, id=db_case.id)
