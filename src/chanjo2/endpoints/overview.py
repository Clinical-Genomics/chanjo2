import logging
from os import path

from fastapi import APIRouter, Request, Depends
from fastapi import Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from chanjo2.dbutil import get_session
from chanjo2.demo import DEMO_COVERAGE_QUERY_DATA
from chanjo2.meta.handle_report_contents import get_report_data, get_gene_overview_data
from chanjo2.models.pydantic_models import ReportQuery, GeneReportForm, GeneCoverage

LOG = logging.getLogger("uvicorn.access")


def get_templates_path() -> str:
    """Returns the absolute path to the templates folder of this app."""
    APP_ROOT: str = path.abspath(path.join(path.dirname(__file__), ".."))
    return path.join(APP_ROOT, "templates")


templates = Jinja2Templates(directory=get_templates_path())
router = APIRouter()


@router.get("/overview/demo", response_class=HTMLResponse)
async def demo_overview(request: Request, db: Session = Depends(get_session)):
    """Return a demo genes overview page over a list of genes for a list of samples."""

    overview_query = ReportQuery(**DEMO_COVERAGE_QUERY_DATA)
    overview_content: dict = get_report_data(
        query=overview_query, session=db, is_overview_report=True
    )
    return templates.TemplateResponse(
        "overview.html",
        {
            "request": request,
            "extras": overview_content["extras"],
            "levels": overview_content["levels"],
            "incomplete_coverage_rows": overview_content["incomplete_coverage_rows"],
        },
    )


@router.post("/overview", response_class=HTMLResponse)
async def overview(
    request: Request, report_query: ReportQuery, db: Session = Depends(get_session)
):
    """Return the genes overview page over a list of genes for a list of samples."""

    overview_content: dict = get_report_data(
        query=report_query, session=db, is_overview_report=True
    )
    return templates.TemplateResponse(
        "overview.html",
        {
            "request": request,
            "extras": overview_content["extras"],
            "levels": overview_content["levels"],
            "incomplete_coverage_rows": overview_content["incomplete_coverage_rows"],
        },
    )


@router.post("/gene-overview", response_class=HTMLResponse)
async def gene_overview(
    request: Request,
    build: str = Form(...),
    default_level: int = Form(...),
    completeness_thresholds: str = Form(...),
    samples: str = Form(...),
    hgnc_gene_id: int = Form(...),
    interval_type: str = Form(...),
    db: Session = Depends(get_session),
):
    """Returns coverage overview stats for a group of samples over genomic intervals of a single gene."""

    form_data = GeneReportForm(
        build=build,
        default_level=default_level,
        completeness_thresholds=completeness_thresholds,
        samples=samples,
        hgnc_gene_id=hgnc_gene_id,
        interval_type=interval_type,
    )

    gene_overview_content: Dict[str, List[GeneCoverage]] = get_gene_overview_data(
        form_data=form_data, session=db
    )

    return templates.TemplateResponse(
        "gene-overview.html",
        {
            "request": request,
            "interval_type": gene_overview_content["interval_type"],
            "gene": gene_overview_content["gene"],
            "interval_coverage_stats": gene_overview_content[
                "samples_coverage_stats_by_interval"
            ],
            "levels": gene_overview_content["levels"],
        },
    )
