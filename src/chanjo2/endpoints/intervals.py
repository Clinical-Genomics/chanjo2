from typing import List

from chanjo2.dbutil import get_session
from chanjo2.meta.handle_d4.py import single_interval_coverage
from chanjo2.models.pydantic_models import CoverageInterval
from fastapi import APIRouter, Depends, File, HTTPException, Query, status
from sqlmodel import Session, select

router = APIRouter()


@router.get("/intervals/interval/", response_model=CoverageInterval)
def read_single_interval(
    *,
    session: Session = Depends(get_session),
    resource_path: str,
    chromosome: str,
    start: int,
    end: int,
):
    """Return coverage on the given interval for a .d4 resource located on the disk or on a remote server"""

    interval_id = (chromosome, start, end)
    return CoverageInterval(
        chromosome=chromosome,
        start=start,
        end=end,
        interval_id=interval_id,
        mean_coverage=single_interval_coverage(resource_path, interval_id),
    )
