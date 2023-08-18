import logging
from os import path
from typing import Dict, List

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from chanjo2.constants import DEMO_COVERAGE_QUERY_DATA
from chanjo2.crud.intervals import get_genes
from chanjo2.crud.samples import get_samples_coverage_file
from chanjo2.dbutil import Base as SQLModelBase
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_d4 import (
    get_genes_coverage_completeness,
    get_gene_interval_coverage_completeness,
)
from chanjo2.models.pydantic_models import ReportQuery, CoverageInterval
from chanjo2.models.sql_models import Exon as SQLExon
from chanjo2.models.sql_models import Gene as SQLGene
from chanjo2.models.sql_models import Transcript as SQLTranscript

INTERVAL_TYPE_DB_TYPE: Dict[str, SQLModelBase] = {
    "genes": SQLGene,
    "transcripts": SQLTranscript,
    "exons": SQLExon,
}

LOG = logging.getLogger("uvicorn.access")
APP_ROOT: str = path.abspath(path.join(path.dirname(__file__), ".."))
templates = Jinja2Templates(directory=path.join(APP_ROOT, "templates"))
router = APIRouter()


@router.get("/report/demo", response_class=HTMLResponse)
async def demo_report(request: Request, db: Session = Depends(get_session)):
    """Return a coverage report over a list of genes for a list of samples."""

    query = ReportQuery(**DEMO_COVERAGE_QUERY_DATA)
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

    interval_type = INTERVAL_TYPE_DB_TYPE[query.interval_type]

    if interval_type == SQLGene:
        cov_compl_data: List[CoverageInterval] = get_genes_coverage_completeness(
            samples_d4_files=samples_d4_files,
            genes=genes,
            completeness_threholds=query.completeness_thresholds,
        )
    else:
        cov_compl_data: List[
            CoverageInterval
        ] = get_gene_interval_coverage_completeness(
            db=db,
            samples_d4_files=samples_d4_files,
            genes=genes,
            interval_type=SQLTranscript,
            completeness_threholds=query.completeness_thresholds,
        )

    return templates.TemplateResponse(
        "report.html", {"request": request, "data": cov_compl_data}
    )
