import pytest
from chanjo2.dbutil import DEMO_CONNECT_ARGS, get_session
from chanjo2.main import Base, app, engine
from chanjo2.models import sql_models
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = "sqlite:///./test.db"

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


@pytest.fixture(name="test_case")
def test_case() -> dict:
    """Returns a dictionary corresponding to a case record."""
    return {"name": "123", "display_name": "case_123"}


@pytest.fixture(name="test_sample")
def test_sample() -> dict:
    """Returns a dictionary used to create a sample in the database."""
    return {"name": "abc", "display_name": "sample_abc"}


@pytest.fixture(name="db_case")
def db_case(test_case) -> sql_models.Case:
    """Returns an object corresponding to a sql_models.Case"""
    return sql_models.Case(
        name=test_case["name"], display_name=test_case["display_name"]
    )


@pytest.fixture(name="db_sample")
def db_sample(test_case, test_sample) -> sql_models.Sample:
    """Returns an object corresponding to a sql_models.Sample"""
    return sql_models.Sample(
        name=test_sample["name"],
        display_name=test_sample["display_name"],
        case_id=1,
        coverage_file_path="a_file.d4",
    )
