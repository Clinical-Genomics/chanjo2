import os
from functools import wraps

from fastapi import HTTPException, Request

from chanjo2.security import verify_token

REQUIRE_AUTH = os.getenv("REQUIRE_AUTH") == "Y"


def check_auth():
    def decorator(route_handler):
        @wraps(route_handler)
        async def wrapper(request: Request, *args, **kwargs):
            if REQUIRE_AUTH:
                # Just verify the token, raise HTTPException if invalid
                await verify_token(request)
            return await route_handler(request, *args, **kwargs)

        return wrapper

    return decorator
