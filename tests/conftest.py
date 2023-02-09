from typing import Dict

import pytest
from chanjo2.dbutil import DEMO_CONNECT_ARGS, get_session
from chanjo2.main import Base, app, engine
from chanjo2.models import sql_models
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = "sqlite:///./test.db"
CASE_NAME = "123"
CASE_DISPLAY_NAME = "case_123"
SAMPLE_NAME = "abc"
SAMPLE_DISPLAY_NAME = "sample_abc"
CASES_ENDPOINT = "/cases/"
SAMPLES_ENDPOINT = "/samples/"
WRONG_COVERAGE_PATH = "a_file.d4"

engine = create_engine(TEST_DB, connect_args=DEMO_CONNECT_ARGS)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="test_db")
def test_db_fixture() -> str:
    """Returns a string representing the path to the test database file"""
    return TEST_DB


@pytest.fixture(name="session")
def session_fixture() -> sessionmaker:
    """Returns an obect of type sqlalchemy.orm.session.sessionmaker"""

    # Create the database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(name="cases_endpoint")
def cases_endpoint() -> str:
    """Returns cases app endpoint"""
    return CASES_ENDPOINT


@pytest.fixture(name="samples_endpoint")
def samples_endpoint() -> str:
    """Returns cases app endpoint"""
    return SAMPLES_ENDPOINT


@pytest.fixture(name="client")
def client_fixture(session) -> TestClient:
    """Returns a fastapi.testclient.TestClient used to test the app endpoints"""

    def _override_get_db():
        try:
            db = session
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = _override_get_db

    return TestClient(app)


@pytest.fixture(name="raw_case")
def raw_case() -> Dict[str, str]:
    """Returns a dictionary corresponding to a case record."""
    return {"name": CASE_NAME, "display_name": CASE_DISPLAY_NAME}


@pytest.fixture(name="raw_sample")
def raw_sample() -> Dict[str, str]:
    """Returns a dictionary used to create a sample in the database."""
    return {"name": SAMPLE_NAME, "display_name": SAMPLE_DISPLAY_NAME}


@pytest.fixture(name="db_case")
def db_case(raw_case) -> sql_models.Case:
    """Returns an object corresponding to a sql_models.Case."""
    return sql_models.Case(name=raw_case["name"], display_name=raw_case["display_name"])


@pytest.fixture(name="db_sample")
def db_sample(raw_case, raw_sample) -> sql_models.Sample:
    """Returns an object corresponding to a sql_models.Sample."""
    return sql_models.Sample(
        name=raw_sample["name"],
        display_name=raw_sample["display_name"],
        case_id=1,
        coverage_file_path=WRONG_COVERAGE_PATH,
    )


@pytest.fixture(name="wrong_coverage_path")
def wrong_coverage_path() -> str:
    """Returns the path to a file that doesn't exist on disk"""
    return WRONG_COVERAGE_PATH
