import logging
from os import path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from chanjo2.dbutil import get_session
from chanjo2.models.pydantic_models import ReportQuery

LOG = logging.getLogger("uvicorn.access")

APP_ROOT: str = path.abspath(path.join(path.dirname(__file__), ".."))

templates = Jinja2Templates(directory=path.join(APP_ROOT, "templates"))

router = APIRouter()


@router.post("/report/", response_class=HTMLResponse)
async def report(query: ReportQuery, db: Session = Depends(get_session)):
    """Return a coverage report over a list of genes for a list of  samples."""

    samples_d4_files: Tuple[str, D4File] = get_samples_coverage_file(
        db=db, samples=query.samples, case=query.case
    )

    genes: List[SQLGene] = get_genes(
        db=db,
        build=query.build,
        ensembl_ids=query.ensembl_gene_ids,
        hgnc_ids=query.hgnc_gene_ids,
        hgnc_symbols=query.hgnc_gene_symbols,
        limit=None,
    )

    LOG.warning(query.interval_type)

    return templates.TemplateResponse("item.html")
