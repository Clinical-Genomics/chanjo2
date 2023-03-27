from typing import List, Optional, Tuple

from chanjo2.constants import WRONG_BED_FILE_MSG, WRONG_COVERAGE_FILE_MSG
from chanjo2.crud.intervals import get_genes
from chanjo2.dbutil import get_session
from chanjo2.meta.handle_bed import parse_bed
from chanjo2.meta.handle_d4 import (
    interval_coverage,
    intervals_coverage,
    set_d4_file,
    set_interval,
)
from chanjo2.meta.handle_load_intervals import update_genes
from chanjo2.models.pydantic_models import Builds, CoverageInterval, Gene, Interval
from fastapi import APIRouter, Depends, File, HTTPException, Response, status
from fastapi.responses import JSONResponse
from pyd4 import D4File
from sqlmodel import Session, select

router = APIRouter()


@router.get("/intervals/coverage/d4/interval/", response_model=CoverageInterval)
def d4_interval_coverage(
    coverage_file_path: str,
    chromosome: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
    session: Session = Depends(get_session),
):
    """Return coverage on the given interval for a D4 resource located on the disk or on a remote server."""

    interval: Tuple[str, Optional[int], Optional[int]] = set_interval(
        chrom=chromosome, start=start, end=end
    )
    try:
        d4_file: D4File = set_d4_file(coverage_file_path)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    return CoverageInterval(
        chromosome=chromosome,
        start=start,
        end=end,
        interval=interval,
        mean_coverage=interval_coverage(d4_file, interval),
    )


@router.post(
    "/intervals/coverage/d4/interval_file/", response_model=List[CoverageInterval]
)
def d4_intervals_coverage(coverage_file_path: str, bed_file: bytes = File(...)):
    """Return coverage on the given intervals for a D4 resource located on the disk or on a remote server."""

    try:
        d4_file: D4File = set_d4_file(coverage_file_path=coverage_file_path)
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=WRONG_COVERAGE_FILE_MSG,
        )

    try:
        intervals: List[Tuple[str, Optional[int], Optional[int]]] = parse_bed(
            bed_file=bed_file
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=WRONG_BED_FILE_MSG,
        )

    return intervals_coverage(d4_file=d4_file, intervals=intervals)


@router.post("/intervals/load/genes/{build}")
async def load_genes(
    build: Builds, session: Session = Depends(get_session)
) -> Response:
    """Load genes of in the given genome build."""
    n_loaded_genes: int = await update_genes(build, session)
    return JSONResponse(
        content={"detail": f"{n_loaded_genes} genes loaded into the database"}
    )


@router.get("/intervals/genes/{build}")
def genes(build: Builds, session: Session = Depends(get_session)) -> List[Gene]:
    """Load genes of in the given genome build."""
    return get_genes(db=session, build=build)
