def test_create_case(client):
    """Test the endpoint used to create a case object"""
    # GIVEN a new case to be created in the database
    test_case = {"name": "case_id", "display_name": "case_name"}
    response = client.post("/cases", json=test_case)
    assert response.status_code == 200
    assert response.json == test_case
