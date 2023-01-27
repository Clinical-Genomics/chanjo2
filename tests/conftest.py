import pytest
from chanjo2.main import Base, app, create_db_and_tables, engine
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = "sqlite:///./test.db"


@pytest.fixture(name="test_db")
def test_db_fixture():
    """Returns a string representing the path to the test database file"""
    return TEST_DB


@pytest.fixture(name="session")
def session_fixture():
    """Returns an obect of type sqlalchemy.orm.session.sessionmaker"""
    engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="client")
def client_fixture(session):
    """Returns a fastapi.testclient.TestClient used to test the app endpoints"""

    def override_get_db():
        try:
            db = session
            yield db
        finally:
            db.close()

    app.dependency_overrides[create_db_and_tables] = override_get_db

    return TestClient(app)
