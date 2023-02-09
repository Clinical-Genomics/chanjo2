from typing import List, Union

from chanjo2.models.pydantic_models import CaseCreate, Sample, SampleCreate
from chanjo2.models.sql_models import Case as SQLCase
from chanjo2.models.sql_models import Sample as SQLSample
from sqlalchemy.orm import Session


def get_samples(db: Session, skip: int = 0, limit: int = 100) -> List[Sample]:
    """Return all samples."""
    return db.query(SQLSample).offset(skip).limit(limit).all()


def get_case_samples(db: Session, case_name: str) -> List[Sample]:
    """Return all samples for a given case name."""
    return db.query(SQLSample).join(SQLCase).filter(SQLCase.name == case_name).all()


def get_sample(db: Session, sample_name: str) -> Sample:
    """Return a specific sample by name."""
    return db.query(SQLSample).filter(SQLSample.name == sample_name).first()


def create_sample_in_case(db: Session, sample: SampleCreate) -> Union[Sample, None]:
    """Create a sample"""
    # Check if sample's case exists first
    case_obj = db.query(SQLCase).filter(SQLCase.name == sample.case_name).first()
    if not case_obj:
        return

    # Insert new sample
    db_sample = SQLSample(
        name=sample.name,
        display_name=sample.display_name,
        case_id=case_obj.id,
        coverage_file_path=sample.coverage_file_path,
    )
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample
