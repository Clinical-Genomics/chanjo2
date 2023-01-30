from chanjo2.models import pydantic_models, sql_models
from sqlalchemy.orm import Session


### Case utils
def get_cases(db: Session, skip: int = 0, limit: int = 100):
    """Return all cases"""
    return db.query(sql_models.Case).offset(skip).limit(limit).all()


def get_case(db: Session, case_name: str):
    """Return a specific case by providing its ID"""
    return db.query(sql_models.Case).filter(sql_models.Case.name == case_name).first()


def create_case(db: Session, case: pydantic_models.CaseCreate):
    """Create a case"""
    db_sample = sql_models.Case(id=case.id, display_name=case.display_name)
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample


### Sample utils
def get_samples(db: Session, skip: int = 0, limit: int = 100):
    """Return all samples"""
    return db.query(sql_models.Sample).offset(skip).limit(limit).all()


def get_case_samples(db: Session, case_id: int):
    """Return all samples for a given case ID"""
    return db.query(sql_models.Sample).filter(sql_models.Sample.id == case_id)


def get_sample(db: Session, sample_id: int):
    """Return a specific sample by its ID"""
    return db.query(sql_models.Sample).filter(sql_models.Sample.id == sample_id).first()


def create_case_sample(db: Session, item: pydantic_models.SampleCreate, case_id: int):
    """Create a sample"""
    db_sample = sql_models.Sample(**sample.dict(), case_id=case_id)
    db.add(db_sample)
    db.commit()
    db.refresh(db_sample)
    return db_sample
