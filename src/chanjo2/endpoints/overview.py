from os import path
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic_core._pydantic_core import ValidationError
from sqlalchemy.orm import Session
from starlette.datastructures import FormData
from typing_extensions import Annotated

from chanjo2.constants import DEFAULT_COVERAGE_LEVEL
from chanjo2.dbutil import get_session
from chanjo2.demo import DEMO_COVERAGE_QUERY_FORM
from chanjo2.meta.handle_report_contents import (
    get_gene_overview_coverage_stats,
    get_mane_overview_coverage_stats,
    get_report_data,
)
from chanjo2.models.pydantic_models import (
    Builds,
    GeneCoverage,
    GeneReportForm,
    IntervalType,
    ReportQuery,
)


def get_templates_path() -> str:
    """Returns the absolute path to the templates folder of this app."""
    APP_ROOT: str = path.abspath(path.join(path.dirname(__file__), ".."))
    return path.join(APP_ROOT, "templates")


templates = Jinja2Templates(directory=get_templates_path())
router = APIRouter()


@router.get("/overview/demo", response_class=HTMLResponse)
async def demo_overview(request: Request, db: Session = Depends(get_session)):
    """Return a demo genes overview page over a list of genes for a list of samples."""

    overview_query = ReportQuery.as_form(DEMO_COVERAGE_QUERY_FORM)
    overview_content: dict = get_report_data(
        query=overview_query, session=db, is_overview=True
    )
    return templates.TemplateResponse(
        request=request,
        name="overview.html",
        context={
            "extras": overview_content["extras"],
            "levels": overview_content["levels"],
            "incomplete_coverage_rows": overview_content["incomplete_coverage_rows"],
        },
    )


@router.post("/overview", response_class=HTMLResponse)
async def overview(
    request: Request,
    build=Annotated[Builds, Form(...)],
    samples=Annotated[str, Form(...)],
    interval_type=Annotated[IntervalType, Form(...)],
    completeness_thresholds=Annotated[Optional[str], Form(None)],
    ensembl_gene_ids=Annotated[Optional[str], Form(None)],
    hgnc_gene_ids=Annotated[Optional[str], Form(None)],
    hgnc_gene_symbols=Annotated[Optional[str], Form(None)],
    default_level=Annotated[Optional[int], Form(DEFAULT_COVERAGE_LEVEL)],
    db: Session = Depends(get_session),
):
    """Return the genes overview page over a list of genes for a list of samples."""
    try:
        overview_query = ReportQuery.as_form(await request.form())

    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ve.json(),
        )

    overview_content: dict = get_report_data(
        query=overview_query, session=db, is_overview=True
    )
    return templates.TemplateResponse(
        request=request,
        name="overview.html",
        context={
            "extras": overview_content["extras"],
            "levels": overview_content["levels"],
            "incomplete_coverage_rows": overview_content["incomplete_coverage_rows"],
        },
    )


@router.post("/gene_overview", response_class=HTMLResponse)
async def gene_overview(
    request: Request,
    db: Session = Depends(get_session),
):
    """Returns coverage overview stats for a group of samples over genomic intervals of a single gene."""
    form_data: FormData = await request.form()
    form_dict: dict = jsonable_encoder(form_data)
    validated_form = GeneReportForm(**form_dict)

    gene_overview_content: Dict[str, List[GeneCoverage]] = (
        get_gene_overview_coverage_stats(form_data=validated_form, session=db)
    )

    return templates.TemplateResponse(
        request=request, name="gene-overview.html", context=gene_overview_content
    )


@router.get("/mane_overview/demo", response_class=HTMLResponse)
async def demo_mane_overview(
    request: Request,
    db: Session = Depends(get_session),
):
    """Returns coverage overview stats for a group of samples over MANE transcripts of a demo list of genes."""
    overview_query = ReportQuery.as_form(DEMO_COVERAGE_QUERY_FORM)
    overview_query.interval_type = IntervalType.TRANSCRIPTS
    overview_query.build = Builds.build_38

    return templates.TemplateResponse(
        request=request,
        name="mane-overview.html",
        context=get_mane_overview_coverage_stats(query=overview_query, session=db),
    )


@router.post("/mane_overview", response_class=HTMLResponse)
async def mane_overview(
    request: Request,
    build=Annotated[Builds, Form(Builds.build_38)],
    samples=Annotated[str, Form(...)],
    interval_type=Annotated[IntervalType, Form(IntervalType.TRANSCRIPTS)],
    completeness_thresholds=Annotated[Optional[str], Form(None)],
    ensembl_gene_ids=Annotated[Optional[str], Form(None)],
    hgnc_gene_ids=Annotated[Optional[str], Form(None)],
    hgnc_gene_symbols=Annotated[Optional[str], Form(None)],
    default_level=Annotated[Optional[int], Form(DEFAULT_COVERAGE_LEVEL)],
    db: Session = Depends(get_session),
):
    """Returns coverage overview stats for a group of samples over MANE transcripts of a list of genes."""
    try:
        overview_query = ReportQuery.as_form(await request.form())

    except ValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ve.json(),
        )

    return templates.TemplateResponse(
        request=request,
        name="mane-overview.html",
        context=get_mane_overview_coverage_stats(query=overview_query, session=db),
    )
