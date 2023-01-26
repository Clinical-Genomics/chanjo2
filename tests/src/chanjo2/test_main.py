from chanjo2 import __version__


def test_heartbeat(client):
    """Test the function that returns a message if server is running"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": f"Chanjo2 v{__version__} is up and running!"}
