from typing import Optional

from chanjo2.dbutil import get_session
from chanjo2.meta.handle_d4 import interval_coverage, set_d4_file, set_interval
from chanjo2.models.pydantic_models import CoverageInterval
from fastapi import APIRouter, Depends, File, HTTPException, Query, status
from pyd4 import D4File
from sqlmodel import Session, select

router = APIRouter()


@router.get("/intervals/interval/", response_model=CoverageInterval)
def read_single_interval(
    *,
    session: Session = Depends(get_session),
    resource_path: str,
    chromosome: str,
    start: Optional[int] = None,
    end: Optional[int] = None,
):
    """Return coverage on the given interval for a .d4 resource located on the disk or on a remote server"""

    interval: tuple = set_interval(chromosome, start, end)
    d4_file: D4File = set_d4_file(resource_path)
    return CoverageInterval(
        chromosome=chromosome,
        start=start,
        end=end,
        interval=interval,
        mean_coverage=interval_coverage(d4_file, interval),
    )
