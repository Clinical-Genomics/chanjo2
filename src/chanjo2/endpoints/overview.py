from os import path

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from chanjo2.dbutil import get_session
from chanjo2.demo import DEMO_OVERVIEW_QUERY_DATA
from chanjo2.meta.handle_overview_content import get_overview_data
from chanjo2.models.pydantic_models import GeneralReportQuery


def get_templates_path() -> str:
    """Returns the absolute path to the templates folder of this app."""
    APP_ROOT: str = path.abspath(path.join(path.dirname(__file__), ".."))
    return path.join(APP_ROOT, "templates")


templates = Jinja2Templates(directory=get_templates_path())
router = APIRouter()


@router.get("/overview/demo", response_class=HTMLResponse)
async def demo_overview(request: Request, db: Session = Depends(get_session)):
    """Return a demo genes overview page over a list of genes for a list of samples."""

    overview_query = GeneralReportQuery(**DEMO_OVERVIEW_QUERY_DATA)
    overview_content: dict = get_overview_data(query=overview_query, session=db)
    return templates.TemplateResponse(
        "overview.html",
        {
            "request": request,
            "extras": overview_content["extras"],
            "levels": overview_content["levels"],
            "samples_coverage_stats": overview_content["samples_coverage_stats"]
        },
    )
