import logging
import time
from os import path
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic_core._pydantic_core import ValidationError
from sqlalchemy.orm import Session
from typing_extensions import Annotated

from chanjo2.constants import DEFAULT_COVERAGE_LEVEL
from chanjo2.dbutil import get_session
from chanjo2.demo import DEMO_COVERAGE_QUERY_FORM
from chanjo2.meta.handle_report_contents import get_report_data
from chanjo2.models.pydantic_models import Builds, IntervalType, ReportQuery


def get_templates_path() -> str:
    """Returns the absolute path to the templates folder of this app."""
    APP_ROOT: str = path.abspath(path.join(path.dirname(__file__), ".."))
    return path.join(APP_ROOT, "templates")


LOG = logging.getLogger(__name__)
templates: Jinja2Templates = Jinja2Templates(directory=get_templates_path())
router = APIRouter()


@router.get("/report/demo", response_class=HTMLResponse)
async def demo_report(request: Request, db: Session = Depends(get_session)):
    """Return a demo coverage report over a list of genes for a list of samples."""

    report_query = ReportQuery.as_form(DEMO_COVERAGE_QUERY_FORM)
    report_content: Dict = get_report_data(query=report_query, session=db)
    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context={
            "levels": report_content["levels"],
            "extras": report_content["extras"],
            "sex_rows": report_content["sex_rows"],
            "completeness_rows": report_content["completeness_rows"],
            "default_level_completeness_rows": report_content[
                "default_level_completeness_rows"
            ],
            "interval_type": report_query.interval_type.value,
            "errors": report_content["errors"],
        },
    )


@router.post("/report", response_class=HTMLResponse)
async def report(
    request: Request,
    build=Annotated[Builds, Form(...)],
    samples=Annotated[str, Form(...)],
    interval_type=Annotated[IntervalType, Form(...)],
    completeness_thresholds=Annotated[Optional[str], Form(None)],
    ensembl_gene_ids=Annotated[Optional[str], Form(None)],
    hgnc_gene_ids=Annotated[Optional[str], Form(None)],
    hgnc_gene_symbols=Annotated[Optional[str], Form(None)],
    case_display_name=Annotated[Optional[str], Form(None)],
    panel_name=Annotated[Optional[str], Form("Custom panel")],
    default_level=Annotated[Optional[int], Form(DEFAULT_COVERAGE_LEVEL)],
    db: Session = Depends(get_session),
):
    """Return a coverage report over a list of genes for a list of samples."""

    start_time = time.time()
    try:
        report_query = ReportQuery.as_form(await request.form())
    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ve.json(),
        )

    report_content: dict = get_report_data(query=report_query, session=db)
    LOG.debug(f"Time to compute stats: {time.time() - start_time} seconds.")
    return templates.TemplateResponse(
        request=request,
        name="report.html",
        context={
            "levels": report_content["levels"],
            "extras": report_content["extras"],
            "sex_rows": report_content["sex_rows"],
            "completeness_rows": report_content["completeness_rows"],
            "default_level_completeness_rows": report_content[
                "default_level_completeness_rows"
            ],
            "interval_type": report_query.interval_type.value,
            "errors": report_content["errors"],
        },
    )
