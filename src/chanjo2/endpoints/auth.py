import os

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse

router = APIRouter()

# Init OAuth
oauth = OAuth()
oidc_client_id = os.getenv("OIDC_CLIENT_ID")

if oidc_client_id:
    oauth.register(
        name="oidc",
        client_id=os.getenv("OIDC_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url=os.getenv("OIDC_DISCOVERY_URL"),
        client_kwargs={"scope": "openid email profile"},
    )
else:
    oauth = None  # OIDC disabled


# --- Dependency ---
def get_current_user(request: Request):
    """"""
    if not oauth:
        return None  # login not enforced
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Login required"
        )
    return user


# --- Routes ---
@router.get("/login")
async def login(request: Request):
    """"""
    if not oauth:
        raise HTTPException(status_code=404, detail="Login not enabled")
    redirect_uri = config("OIDC_REDIRECT_URI")
    return await oauth.oidc.authorize_redirect(request, redirect_uri)


@router.get("/auth/callback")
async def auth_callback(request: Request):
    if not oauth:
        raise HTTPException(status_code=404, detail="Login not enabled")
    token = await oauth.oidc.authorize_access_token(request)
    user = await oauth.oidc.parse_id_token(request, token)
    request.session["user"] = dict(user)
    return RedirectResponse(url="/protected")
