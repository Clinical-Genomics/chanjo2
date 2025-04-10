from chanjo2.demo import HTTP_SERVER_D4_file
from chanjo2.models.pydantic_models import is_valid_url


def test_is_valid_url_false():
    """Test the function that checks if a string is formatted as a URL. Use a malformed URL."""
    assert is_valid_url("https://somefile") is False


def test_is_valid_url_true():
    """Test the function that checks if a string is formatted as a URL. Use a valid URL."""
    assert is_valid_url(HTTP_SERVER_D4_file)
