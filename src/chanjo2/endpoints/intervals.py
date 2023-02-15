from typing import Optional, Tuple

from chanjo2.dbutil import get_session
from chanjo2.meta.handle_d4 import interval_coverage, set_d4_file, set_interval
from chanjo2.models.pydantic_models import WRONG_COVERAGE_FILE_MSG, CoverageInterval
from fastapi import APIRouter, Depends, HTTPException, status
from pyd4 import D4File
from sqlmodel import Session, select

router = APIRouter()


@router.get("/intervals/interval/", response_model=CoverageInterval)
def read_single_interval(
    coverage_file_path: str,
    chromosome: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
    session: Session = Depends(get_session),
):
    """Return coverage on the given interval for a D4 resource located on the disk or on a remote server."""

    interval: Tuple[str, Optional[int], Optional[int]] = set_interval(
        chromosome, start, end
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
