from chanjo2 import __version__
from sqlalchemy import create_engine, inspect

DB_TABLES = ["cases", "interval_tag", "intervals", "samples", "tags"]
SUCCESS_CODE = 200


def test_heartbeat(client):
    """Test the function that returns a message if server is running"""
    # WHEN user makes a call to the heatbeat endpoint
    response = client.get("/")
    # THEN it should return success
    assert response.status_code == SUCCESS_CODE
    # AND the expected message
    assert response.json() == {"message": f"Chanjo2 v{__version__} is up and running!"}


def test_create_db_and_tables(test_db):
    """Test that tables are created correctly when app starts up"""
    # Given a running instance of Chanjo2 (client fixture)

    # WHEN connecting to the same database used by the test app
    engine2 = create_engine(test_db, connect_args={"check_same_thread": False})

    # THEN the expected tables should be found
    insp = inspect(engine2)
    for table in DB_TABLES:
        assert insp.has_table(table)
