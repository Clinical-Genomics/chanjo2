import os
from typing import Any, Dict, List

from fastapi import HTTPException, Request
from jose import jwt
from jose.exceptions import JWTError
from jwt import PyJWKClient

ALGORITHMS: List[str] = ["RS256"]


def get_public_key(token: str) -> str:
    """
    Retrieve the public key from the JWKS endpoint to verify the JWT token signature.

    Args:
        token (str): JWT token string.

    Returns:
        str: The public key used to verify the token.

    Raises:
        RuntimeError: If JWKS_URL environment variable is not set.
    """
    jwks_url = os.environ.get("JWKS_URL")
    if not jwks_url:
        raise RuntimeError("JWKS_URL environment variable not set")

    jwks_client = PyJWKClient(jwks_url)
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return signing_key.key


async def verify_token(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency to verify JWT token passed in form data ('access_token' key).

    Args:
        request (Request): Incoming FastAPI request object.

    Returns:
        Dict[str, Any]: Decoded JWT token payload.

    Raises:
        HTTPException: If access token is missing or token validation fails.
        RuntimeError: If AUDIENCE environment variable is not set.
    """
    form = await request.form()
    token = form.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing access_token")

    try:
        key = get_public_key(token)
        audience = os.environ.get("AUDIENCE")
        if not audience:
            raise RuntimeError("AUDIENCE environment variable not set")

        payload = jwt.decode(token, key=key, algorithms=ALGORITHMS, audience=audience)
        return payload

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token validation error: {e}")
