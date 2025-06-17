import base64
import logging
import os
from typing import Any, Dict

import httpx
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey, RSAPublicNumbers
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt

LOG = logging.getLogger(__name__)

ALGORITHMS = ["RS256"]


def construct_rsa_key(key_data: Dict[str, str]) -> RSAPublicKey:
    """
    Constructs a public RSA key from JWKS `n` and `e`.
    """
    n = int.from_bytes(base64.urlsafe_b64decode(key_data["n"] + "=="), byteorder="big")
    e = int.from_bytes(base64.urlsafe_b64decode(key_data["e"] + "=="), byteorder="big")
    public_numbers = RSAPublicNumbers(e, n)
    return public_numbers.public_key(default_backend())


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Verifies JWT token from cookies or request headers..
    """
    AUDIENCE = os.environ.get("AUDIENCE")
    JWKS_URL = os.environ.get("JWKS_URL")

    if not JWKS_URL or not AUDIENCE:
        # Skip verification in dev mode
        return {"sub": "anonymous", "role": "dev", "auth_skipped": True}

    # Try to get token from Authorization header first
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
    else:
        # Fallback to token in cookies
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
        )

    try:
        # Fetch JWKS
        resp = await httpx.AsyncClient().get(JWKS_URL)
        jwks = resp.json()

        # Get the key that matches the token's `kid`
        unverified_header = jwt.get_unverified_header(token)
        key = next(
            (k for k in jwks["keys"] if k["kid"] == unverified_header["kid"]), None
        )

        if not key:
            raise HTTPException(
                status_code=401, detail="Unable to find matching key in JWKS"
            )

        public_key: RSAPublicKey = construct_rsa_key(key)

        # Decode and validate token
        payload = jwt.decode(
            token,
            public_key,
            algorithms=ALGORITHMS,
            audience=AUDIENCE,
        )
        return payload

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
