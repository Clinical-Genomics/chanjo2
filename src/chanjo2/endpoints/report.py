import logging
from os import path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

LOG = logging.getLogger("uvicorn.access")

APP_ROOT: str = path.abspath(path.join(path.dirname(__file__), ".."))

templates = Jinja2Templates(directory=path.join(APP_ROOT, "templates"))

router = APIRouter()


@router.post("/report/", response_class=HTMLResponse)
async def report(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})
