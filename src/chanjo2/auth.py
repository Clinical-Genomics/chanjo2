import base64
import datetime
import logging
import os
from typing import Dict, Tuple

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


async def get_token(request: Request) -> Tuple[str, datetime.datetime]:
    """
    Validate the OIDC id_token JWT from form/header/cookie.
    Returns:
        token: the validated JWT string
        expires: datetime when the token expires
    """
    AUDIENCE = os.environ.get("AUDIENCE")
    JWKS_URL = os.environ.get("JWKS_URL")

    if not JWKS_URL or not AUDIENCE:
        return None, None

    # Extract token from form > Authorization header > cookie
    form = await request.form()
    token = form.get("id_token")

    auth_header = request.headers.get("Authorization")
    if not token and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()

    if not token:
        token = request.cookies.get("id_token")

    if not token:
        raise HTTPException(status_code=401, detail="Missing id_token")

    try:
        # Optional: log unverified claims
        claims = jwt.get_unverified_claims(token)
        print(f"Received a token with audience: {claims.get('aud')}")

        # Fetch JWKS keys
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URL)
            resp.raise_for_status()
            jwks = resp.json()

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Invalid token header: no kid")

        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(
                status_code=401, detail="Unable to find matching key in JWKS"
            )

        public_key = construct_rsa_key(key)

        # Validate token fully
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=ALGORITHMS,
            audience=AUDIENCE,
            options={"verify_at_hash": False},
        )

        # Compute expiration datetime from `exp` claim
        exp_timestamp = decoded.get("exp")
        if exp_timestamp:
            expires = datetime.datetime.fromtimestamp(
                exp_timestamp, tz=datetime.timezone.utc
            )
        else:
            expires = datetime.datetime.now(
                tz=datetime.timezone.utc
            ) + datetime.timedelta(hours=1)

        return token, expires

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
