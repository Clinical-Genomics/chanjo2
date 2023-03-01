from chanjo2.crud.cases import create_db_case, get_case
from chanjo2.crud.samples import create_sample_in_case
from chanjo2.dbutil import get_session
from chanjo2.demo import d4_demo_path
from chanjo2.models.pydantic_models import CaseCreate, SampleCreate
from chanjo2.models.sql_models import Case
from sqlalchemy.orm import sessionmaker

db: sessionmaker = next(get_session())

DEMO_CASE = {"name": "internal_id", "display_name": "643594"}
DEMO_SAMPLE = {
    "name": "ADM1059A2",
    "display_name": "NA12882",
    "case_name": DEMO_CASE["name"],
    "coverage_file_path": d4_demo_path,
}


def load_demo_data() -> Case:
    """Loads demo data into the database of a demo instance of Chanjo2."""
    load_demo_case()
    load_demo_sample()
    return get_case(db=db, case_name=DEMO_CASE["name"])


def load_demo_case():
    """Load a demo case into the database."""
    case: CaseCreate = CaseCreate(**DEMO_CASE)
    create_db_case(db=db, case=case)


def load_demo_sample():
    """Add a sample to a demo case."""
    sample: SampleCreate = SampleCreate(**DEMO_SAMPLE)
    create_sample_in_case(db=db, sample=sample)
