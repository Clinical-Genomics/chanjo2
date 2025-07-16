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
    Verify and decode the OIDC id_token JWT from request headers, form, or cookies.
    Supports standard OIDC tokens (Google, Keycloak, etc).
    """
    AUDIENCE = os.environ.get("AUDIENCE")
    JWKS_URL = os.environ.get("JWKS_URL")

    if not JWKS_URL or not AUDIENCE:
        return {"sub": "anonymous", "role": "dev", "auth_skipped": True}

    # Extract token from (priority order): form > Authorization header > cookies
    form = await request.form()
    id_token = form.get("id_token")

    auth_header = request.headers.get("Authorization")
    if not id_token and auth_header and auth_header.startswith("Bearer "):
        id_token = auth_header.removeprefix("Bearer ").strip()

    if not id_token:
        id_token = request.cookies.get("id_token")

    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing id_token"
        )

    claims = jwt.get_unverified_claims(id_token)
    print(f"Received a token with audience:{claims.get('aud')}")

    try:
        # Fetch JWKS keys
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URL)
            resp.raise_for_status()
            jwks = resp.json()

        # Extract kid from unverified token header
        unverified_header = jwt.get_unverified_header(id_token)

        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Invalid token header: no kid")

        # Find matching key
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(
                status_code=401, detail="Unable to find matching key in JWKS"
            )

        # Construct public key object for verification
        public_key = construct_rsa_key(key)

        # Decode & validate token
        payload = jwt.decode(
            id_token,
            public_key,
            algorithms=ALGORITHMS,
            audience=AUDIENCE,
            options={"verify_at_hash": False},  # disables at_hash validation
        )
        return payload

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
