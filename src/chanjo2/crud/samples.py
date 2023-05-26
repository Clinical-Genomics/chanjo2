from typing import List, Optional

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, query
from sqlalchemy.sql.expression import Delete

from chanjo2.crud.cases import filter_cases_by_name
from chanjo2.models.pydantic_models import SampleCreate
from chanjo2.models.sql_models import Case as SQLCase
from chanjo2.models.sql_models import CaseSample
from chanjo2.models.sql_models import Sample as SQLSample


def _filter_samples_by_name(
    samples: query.Query,
    sample_names: List[str],
) -> query.Query:
    """Filter samples by sample name."""
    return samples.filter(SQLSample.name.in_(sample_names))


def get_samples(db: Session, limit: int = 100) -> List[SQLSample]:
    """Return all samples."""
    return db.query(SQLSample).limit(limit).all()


def get_samples_by_name(db: Session, sample_names: List[str]) -> List[SQLSample]:
    """Filter samples by a list of names."""
    query = db.query(SQLSample)
    return _filter_samples_by_name(samples=query, sample_names=sample_names).all()


def get_case_samples(db: Session, case_name: str) -> List:
    """Return all samples for a given case name."""

    db_case: SQLCase = db.query(SQLCase).where(SQLCase.name == case_name).first()
    if db_case:
        return db_case.samples
    return []


def get_sample(db: Session, sample_name: str) -> SQLSample:
    """Return a specific sample by name."""
    pipeline = {"filter_samples_by_name": _filter_samples_by_name}
    query = db.query(SQLSample)

    return pipeline["filter_samples_by_name"](
        samples=query, sample_names=[sample_name]
    ).first()


def create_sample_in_case(db: Session, sample: SampleCreate) -> Optional[SQLSample]:
    """Create a sample."""
    # Check if case exists first
    pipeline = {"filter_cases_by_name": filter_cases_by_name}
    query = db.query(SQLCase)
    db_case: SQLCase = pipeline["filter_cases_by_name"](query, sample.case_name)
    if not db_case:
        return f"Could not find a case with name: {sample.case_name}"

    # Check if sample already exists
    db_sample: SQLSample = get_sample(db=db, sample_name=sample.name)
    if db_sample is None:  # Create it
        db_sample = SQLSample(
            name=sample.name,
            display_name=sample.display_name,
            track_name=sample.track_name,
            coverage_file_path=sample.coverage_file_path,
        )
        db.add(db_sample)
        db.commit()
        db.refresh(db_sample)

    # Connect sample to existing case
    try:
        statement: Insert = CaseSample.insert().values(
            case_id=db_case.id, sample_id=db_sample.id
        )
        db.execute(statement)
        db.commit()
        db.refresh(db_case)
        return db_sample
    except IntegrityError:
        return "Sample already connected to given case."


def delete_sample(db: Session, sample_name: str) -> int:
    """Delete sample with the supplied name."""
    delete_stmt: Delete = delete(SQLSample).where(SQLSample.name == sample_name)
    result = db.execute(delete_stmt)
    db.commit()
    return result.rowcount
