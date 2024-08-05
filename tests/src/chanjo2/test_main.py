from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from chanjo2 import __version__
from chanjo2.dbutil import DEMO_CONNECT_ARGS

DB_TABLES = ["intervals", "genes"]


def test_heartbeat(client: TestClient):
    """Test the function that returns a message if server is running."""
    # WHEN user makes a call to the heatbeat endpoint
    response = client.get("/")
    # THEN it should return success
    assert response.status_code == status.HTTP_200_OK
    # AND the expected message
    assert response.json() == {"message": f"Chanjo2 v{__version__} is up and running!"}


def test_create_db_and_tables(test_db: str):
    """Test that tables are created correctly when app starts up."""
    # Given a running instance of Chanjo2

    # WHEN connecting to the same database used by the test app
    engine = create_engine(test_db, connect_args=DEMO_CONNECT_ARGS)

    # THEN the expected tables should be found
    insp = inspect(engine)
    for table in DB_TABLES:
        assert insp.has_table(table)
