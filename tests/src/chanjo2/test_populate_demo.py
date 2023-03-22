from chanjo2.crud.cases import get_cases
from chanjo2.dbutil import get_session
from chanjo2.main import app
from chanjo2.models.sql_models import Case
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

client = TestClient(app)
db: sessionmaker = next(get_session())


def test_load_demo_data():
    """Test loading demo data."""

    # WHEN the app is launched
    with TestClient(app) as client:
        # THEN a demo case should be found in the database
        cases: List[Case] = get_cases(db)
        assert isinstance(cases[0], Case)