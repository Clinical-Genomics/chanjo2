import pytest
from chanjo2.main import Base, app, create_db_and_tables, engine
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB = "sqlite:///./test.db"


@pytest.fixture(name="testdb")
def testdb_fixture():
    return TEST_DB


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="client")
def client_fixture(session):
    def override_get_db():
        try:
            db = session
            yield db
        finally:
            db.close()

    app.dependency_overrides[create_db_and_tables] = override_get_db

    return TestClient(app)
