import logging
from os import path
from typing import Dict

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from chanjo2.dbutil import get_session
from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA
from chanjo2.meta.handle_report_contents import get_report_data
from chanjo2.models.pydantic_models import ReportQuery


def get_templates_path() -> str:
    """Returns the absolute path to the templates folder of this app."""
    APP_ROOT: str = path.abspath(path.join(path.dirname(__file__), ".."))
    return path.join(APP_ROOT, "templates")


LOG = logging.getLogger("uvicorn.access")
templates: Jinja2Templates = Jinja2Templates(directory=get_templates_path())
router = APIRouter()


@router.get("/report/demo", response_class=HTMLResponse)
async def demo_report(request: Request, db: Session = Depends(get_session)):
    """Return a coverage report over a list of genes for a list of samples."""

    report_query = ReportQuery(**DEMO_COVERAGE_QUERY_DATA)
    data: Dict = get_report_data(query=report_query, session=db)
    return templates.TemplateResponse(
        "report.html",
        {
            "request": request,
            "extras": data["extras"],
            "sex_rows": data["sex_rows"],
        },
    )
